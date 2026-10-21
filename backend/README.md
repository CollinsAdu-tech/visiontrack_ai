# VisionTrack AI -- Backend

Phase 1 status: project foundation only (health check + config).
No detection or tracking code yet -- that's Phase 2 onward.

## Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/config
curl -F "file=@sample.jpg" http://localhost:8000/detect/image
curl -F "file=@sample.mp4" http://localhost:8000/detect/video
curl -F "file=@sample.mp4" http://localhost:8000/track/video
```

Expected:

```json
{"status": "ok", "app_name": "VisionTrack AI", "version": "0.1.0"}
```

## Test

```bash
pytest
```
