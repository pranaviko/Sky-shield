# Sky Shield - Full Stack (Generated)

This archive contains a ready-to-run full-stack Sky Shield prototype:
- Backend: Flask + SocketIO, YOLOv8 (ultralytics), DeepSORT (deep_sort_realtime)
- Frontend: React + socket.io-client (simple viewer)
- Postgres DB (dockerized)
- Docker Compose for quick startup

Steps:
1. Place YOLOv8 weights in backend/models/ (e.g. yolov8n.pt)
2. (Optional) Customize .env or docker-compose envs
3. Build & run:
   ```
   docker compose up --build
   ```
4. Create admin user:
   ```
   docker compose exec backend python create_admin.py
   ```
5. Open frontend: http://localhost:3000

Notes:
- DeepSORT requires `deep_sort_realtime` which is included in requirements.txt.
- For GPU support / Jetson: change `DEVICE=cuda` and use a CUDA-enabled base image. You may need to install PyTorch & other GPU deps appropriate to your platform.
- This generated repo is a starting point — test carefully, secure secrets, and harden for production.


## Updates included in this package
- Replaced tracker with **Norfair** for robust, lightweight tracking (configurable IoU distance).
- Added full Camera Management UI (create/edit/delete cameras, set per-camera infer interval & confidence thresholds).
- Added `backend/Dockerfile.jetson` — a Jetson-optimized Dockerfile example (use matching L4T/PyTorch base image and test on-device).

**Notes:** On Jetson, install proper PyTorch + CUDA matching your JetPack version. The provided Dockerfile is a template — you may need to adjust base image tags.

- Added **incident suppression**: same track_id will not trigger a new alert within 10s window (tunable in detector).

- Added **User Management**: Admins can create/delete users and set roles from dashboard.
