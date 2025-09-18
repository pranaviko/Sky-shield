import cv2
import threading
import time
import os
from ultralytics import YOLO
# Norfair for lightweight tracking (pip install norfair)
from norfair import Detection, Tracker
from models import Camera
from utils import save_thumbnail

class CameraWorker:
    def __init__(self, cam: Camera, weights, device='cpu'):
        self.cam = cam
        self.src = cam.source
        self.name = cam.name
        self.enabled = bool(cam.enabled)
        self.conf_threshold = cam.conf_threshold
        self.infer_interval = cam.infer_interval
        self.weights = weights
        self.device = device
        self.cap = None
        self.model = YOLO(weights)
        try:
            self.model.to(device)
        except Exception:
            pass

        # Norfair tracker configuration: distance function = iou-based
        def iou_distance(detection, tracked_object):
            # detection.points and tracked_object.estimate are (x_center, y_center)
            # we'll compute IoU between boxes stored in detection.data and tracked_object.data
            a = detection.data  # [x1,y1,x2,y2]
            b = tracked_object.data
            xx1 = max(a[0], b[0])
            yy1 = max(a[1], b[1])
            xx2 = min(a[2], b[2])
            yy2 = min(a[3], b[3])
            w = max(0., xx2-xx1)
            h = max(0., yy2-yy1)
            inter = w*h
            area1 = (a[2]-a[0])*(a[3]-a[1])
            area2 = (b[2]-b[0])*(b[3]-b[1])
            iou = inter / (area1 + area2 - inter + 1e-6)
            # Norfair expects a distance (lower = closer). We convert iou -> distance
            return 1.0 - iou

        self.tracker = Tracker(
            distance_function=iou_distance,
            distance_threshold=0.7,  # tuneable: lower -> stricter matching
            hit_inertia_min=3,
            hit_inertia_max=30
        )

        self.last_frame = None
        self.results = None
        self.lock = threading.Lock()
        self.running = False
        self.last_alert_time = {}  # track_id -> last timestamp

    def start(self):
        self.cap = cv2.VideoCapture(int(self.src) if str(self.src).isdigit() else self.src)
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while self.running:
            if not self.cap or not self.cap.isOpened():
                time.sleep(1)
                continue
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            with self.lock:
                self.last_frame = frame.copy()
            self._infer_and_track()
            time.sleep(self.infer_interval)

    def _infer_and_track(self):
        with self.lock:
            if self.last_frame is None:
                return
            frame = self.last_frame.copy()
        results = self.model.predict(frame, conf=self.conf_threshold, stream=False)
        detections_for_tracker = []
        det_meta = []

        for r in results:
            for box in r.boxes:
                x1,y1,x2,y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = self.model.names[cls]
                # Norfair Detection stores 'points' but we'll attach bbox in detection.data
                # Use center point for Norfair's internal matching but pass bbox via data
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                det = Detection(points=[cx, cy], scores=[conf], data=[x1,y1,x2,y2])
                detections_for_tracker.append(det)
                det_meta.append({'label': label, 'conf': conf, 'bbox': [x1,y1,x2,y2], 'center': (cx,cy)})

        # update tracker
        tracked_objects = self.tracker.update(detections=detections_for_tracker)

        assignments = []
        for tobj in tracked_objects:
            if tobj.estimate is None:
                continue
            # 'data' is stored in the last seen detection; norfair's tracked_object.last_detection contains data if needed
            last_det = tobj.last_detection
            if last_det is None:
                continue
            bbox = last_det.data
            track_id = tobj.id
            # match to det_meta by bbox equality (since last_detection came from one of them)
            matched = None
            for d in det_meta:
                if d['bbox'] == bbox:
                    matched = d
                    break
            if matched:
                assignments.append({'track_id': track_id, 'label': matched['label'], 'conf': matched['conf'], 'bbox': matched['bbox']})

        with self.lock:
            self.results = {'frame': frame, 'assignments': assignments}

    def get_annotated_jpeg(self):
        with self.lock:
            if self.last_frame is None:
                return None
            frame = self.last_frame.copy()
            results = self.results
        if results:
            for a in results['assignments']:
                x1,y1,x2,y2 = a['bbox']
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.putText(frame, f"{a['label']} id:{a['track_id']} {a['conf']:.2f}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes() if ret else None

    def get_results(self):
        with self.lock:
            return self.results

    def snapshot_and_store_incidents(self, db_session, thumbnail_dir='thumbnails'):
        with self.lock:
            if self.results is None:
                return []
            frame = self.results['frame'].copy()
            assignments = list(self.results['assignments'])
        saved = []
        from models import Incident
        for a in assignments:
                last_ts = self.last_alert_time.get(a['track_id'],0)
                if ts - last_ts < 10:  # suppress alerts within 10s per track
                    continue
                self.last_alert_time[a['track_id']] = ts
            track_id = a['track_id']
            ts = int(time.time())
            fname = f"{self.name}_{track_id}_{ts}.jpg"
            path = os.path.join(thumbnail_dir, fname)
            save_thumbnail(frame, path)
            inc = Incident(camera_id=self.cam.id, label=a['label'], conf=a['conf'], track_id=track_id, thumbnail_path=path)
            db_session.add(inc)
            db_session.commit()
            saved.append(inc)
        return saved
