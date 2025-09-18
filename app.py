import os, time, threading
from flask import Flask, Response, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Camera, Incident
from auth import create_token, authenticate_user, jwt_required
from detector import CameraWorker
import eventlet
eventlet.monkey_patch()

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/skyshield')
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

app = Flask(__name__, static_folder='../frontend/build', static_url_path='/')
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

session = SessionLocal()
weights = os.environ.get('WEIGHTS_PATH', 'models/yolov8n.pt')
device = os.environ.get('DEVICE', 'cpu')

camera_workers = {}
for cam in session.query(Camera).filter_by(enabled=1).all():
    w = CameraWorker(cam, weights, device=device)
    w.start()
    camera_workers[cam.id] = w

def incident_loop():
    s = SessionLocal()
    while True:
        for cam_id, worker in camera_workers.items():
            res = worker.get_results()
            if not res or len(res['assignments'])==0:
                continue
            saved = worker.snapshot_and_store_incidents(s)
            for inc in saved:
                socketio.emit('incident', {
                    'id': inc.id,
                    'camera_id': inc.camera_id,
                    'label': inc.label,
                    'conf': inc.conf,
                    'track_id': inc.track_id,
                    'thumbnail': f"/thumbnails/{inc.thumbnail_path.split('/')[-1]}",
                    'timestamp': inc.timestamp.isoformat()
                })
        time.sleep(float(os.environ.get('INCIDENT_INTERVAL', 1.0)))

@socketio.on('connect')
def on_connect():
    print('client connected')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    db = SessionLocal()
    auth = authenticate_user(db, data.get('username'), data.get('password'))
    if not auth:
        return jsonify({'msg': 'Bad credentials'}), 401
    token = create_token({'id': auth['id'], 'username': auth['username'], 'role': auth['role']})
    return jsonify({'access_token': token})

@app.route('/api/cameras')
@jwt_required(role=['admin','operator','viewer'])
def list_cameras():
    db = SessionLocal()
    cams = db.query(Camera).all()
    out = []
    for c in cams:
        out.append({'id': c.id, 'name': c.name, 'source': c.source, 'enabled': c.enabled, 'conf_threshold': c.conf_threshold, 'infer_interval': c.infer_interval})
    return jsonify(out)


@app.route('/api/cameras', methods=['POST'])
@jwt_required(role=['admin','operator'])
def create_camera():
    data = request.json
    db = SessionLocal()
    cam = Camera(name=data.get('name'), source=data.get('source'),
                 enabled=1 if data.get('enabled', True) else 0,
                 infer_interval=float(data.get('infer_interval', 0.5)),
                 conf_threshold=float(data.get('conf_threshold', 0.45)))
    db.add(cam)
    db.commit()
    # start worker immediately
    w = CameraWorker(cam, weights, device=device)
    w.start()
    camera_workers[cam.id] = w
    return jsonify({'id': cam.id, 'msg': 'created'}), 201

@app.route('/api/cameras/<int:camera_id>', methods=['PUT'])
@jwt_required(role=['admin','operator'])
def update_camera(camera_id):
    data = request.json
    db = SessionLocal()
    cam = db.query(Camera).get(camera_id)
    if not cam:
        return jsonify({'msg':'not found'}), 404
    cam.name = data.get('name', cam.name)
    cam.source = data.get('source', cam.source)
    cam.enabled = 1 if data.get('enabled', cam.enabled) else 0
    cam.infer_interval = float(data.get('infer_interval', cam.infer_interval))
    cam.conf_threshold = float(data.get('conf_threshold', cam.conf_threshold))
    db.commit()
    # restart worker if exists
    worker = camera_workers.get(cam.id)
    if worker:
        worker.running = False
        # give it a moment to stop
        time.sleep(0.2)
    w = CameraWorker(cam, weights, device=device)
    w.start()
    camera_workers[cam.id] = w
    return jsonify({'msg':'updated'})

@app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
@jwt_required(role=['admin'])
def delete_camera(camera_id):
    db = SessionLocal()
    cam = db.query(Camera).get(camera_id)
    if not cam:
        return jsonify({'msg':'not found'}), 404
    # stop worker
    worker = camera_workers.get(cam.id)
    if worker:
        worker.running = False
        camera_workers.pop(cam.id, None)
    db.delete(cam)
    db.commit()
    return jsonify({'msg':'deleted'})


@app.route('/camera/<int:camera_id>/stream')
def mjpeg_stream(camera_id):
    worker = camera_workers.get(camera_id)
    if not worker:
        return 'Camera not found', 404
    def gen():
        while True:
            frame = worker.get_annotated_jpeg()
            if not frame:
                time.sleep(0.1)
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/thumbnails/<path:filename>')
def thumbnails(filename):
    return send_from_directory('thumbnails', filename)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    t = threading.Thread(target=incident_loop, daemon=True)
    t.start()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
