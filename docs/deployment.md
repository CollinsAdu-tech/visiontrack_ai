# Deployment

## Quick start (Docker Compose)

```bash
cp backend/.env.example backend/.env   # required -- compose won't start without it
docker compose up --build
```

- Frontend: <http://localhost>
- Backend API: <http://localhost:8000>

First request to `/detect/image` or `/track/video` downloads
`yolo26n.pt` (a few MB) if it isn't already present in the
`backend_models` volume -- expect a delay on the very first call after
a fresh `docker compose up`, not on every subsequent one. (This relies
on `MODEL_NAME` being a path under `models/`, not a bare filename --
see `backend/app/core/config.py`; an earlier draft of this config had
that wrong, which would have silently defeated the volume mount.)

## What each piece does

- **`backend/Dockerfile`** -- `python:3.11-slim` plus the two system
  libraries `opencv-python` needs at runtime (`libgl1`,
  `libglib2.0-0`) that the slim image doesn't ship by default. Runs a
  single `uvicorn` worker (see **Scaling**, below, for why more than
  one isn't safe yet).
- **`frontend/Dockerfile`** -- multi-stage: builds the Vite bundle,
  then serves it from `nginx:alpine`.
- **`frontend/nginx.conf`** -- proxies `/detect`, `/track`,
  `/results`, `/health`, `/config`, `/outputs` to the backend
  container, and serves the built frontend for everything else.
- **`docker-compose.yml`** -- wires both together, plus named volumes
  so downloaded model weights and processed media survive container
  restarts and rebuilds (without them, every fresh container
  re-downloads `yolo26n.pt`).

## Environment variables

See `backend/.env.example` for the full list with defaults
(`MODEL_NAME`, `DETECTION_CONFIDENCE`, `IOU_THRESHOLD`, `IMAGE_SIZE`,
`TRACKER`, `TRAJECTORY_LENGTH`, the counting-line ratios,
`MAX_UPLOAD_SIZE_MB`, `UPLOAD_DIR`, `OUTPUT_DIR`,
`CORS_ALLOW_ORIGINS`). For a real deployment, at minimum set
`CORS_ALLOW_ORIGINS` to the actual frontend origin -- the default
(`http://localhost:5173`) is a dev-server value.

## Upload size limits live in two places

`MAX_UPLOAD_SIZE_MB` in `backend/.env` controls what the FastAPI app
accepts -- but nginx has its own `client_max_body_size` (set in
`frontend/nginx.conf`, currently `100M` to match the backend default).
If you change one, change the other, or nginx will reject large
uploads with its own `413` before they ever reach the backend's own
validation.

## Production checklist / known gaps

Carried forward honestly from earlier phases, not resolved here:

- **`ResultsStore` is in-memory and per-process** (see
  `docs/architecture.md`). This Dockerfile deliberately runs a single
  `uvicorn` worker for that reason. Running multiple backend
  replicas, or `uvicorn --workers N` with N > 1, means
  `GET /results/{id}` will 404 for results created by a different
  worker. Fix this before scaling horizontally -- swap `ResultsStore`
  for Redis or a database; every route already goes through that one
  interface, so the swap is contained to
  `app/services/results_store.py`.
- **Processing is synchronous** -- a large video upload blocks that
  request (and, with a single worker, blocks other requests too)
  until it finishes. A production deployment handling real traffic
  should move video processing to a background worker/queue (Celery,
  RQ, arq, etc.) and have the frontend poll `GET /results/{id}`
  instead of waiting on one long HTTP call.
- **No authentication** -- add a reverse-proxy auth layer or
  application-level auth before exposing this beyond a trusted
  network.
- **No HTTPS termination configured** -- put a real TLS-terminating
  proxy (e.g. Caddy, or nginx with certbot, or a cloud load balancer)
  in front of this in production; `frontend/nginx.conf` here is HTTP
  only.
- **CI builds both halves, doesn't push images** -- `.github/workflows/ci.yml` runs backend `pytest` and a frontend `npm run build` on every push (a successful Vite build already implies the JSX is syntactically valid), but does not build or push Docker images anywhere. Add that once there's a registry to push to.
- **No real evaluation numbers, and no evaluation gate in CI** -- see
  `docs/evaluation.md`. Don't treat "the container builds and tests
  pass" as "the model performs well" -- those are different claims.

## Model export (future work, not built)

Spec section 44 mentions exporting to ONNX/TensorRT for deployment
optimization. Ultralytics supports this (`model.export(format=...)`),
but nothing here does it yet -- the Dockerfile ships the standard
`.pt` weights and runs standard PyTorch inference.
