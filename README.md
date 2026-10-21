# VisionTrack AI

> See. Track. Understand.

A computer-vision application that detects objects in images and
video, tracks their identities across frames, and turns visual
movement into analytics: object counts, entries, exits, and
trajectories. Built as a demonstration of a complete computer-vision
engineering pipeline (detection -> tracking -> counting -> analytics
-> dashboard), not a from-scratch model -- see **Tech stack** below.

**Status: all 13 phases complete.** Full phase-by-phase changelog at
the bottom of this file.

## Features

- Object detection in images and video (pretrained YOLO26n)
- Multi-object tracking with persistent IDs across video frames (ByteTrack)
- Bounded trajectory history per tracked object, drawn on the output video
- Configurable virtual counting line with entry/exit detection and
  duplicate-count prevention
- Per-class object analytics (counts, current objects, unique tracked
  objects, processing FPS)
- React dashboard: upload, run, view annotated results and analytics
- Evaluation harness for detection (mAP), tracking (ID switches,
  fragmentation), and counting accuracy -- see `docs/evaluation.md`

## Tech stack

| Layer | Choice |
|---|---|
| Detection | YOLO26n (pretrained, Ultralytics) |
| Tracking | ByteTrack (Ultralytics built-in), swappable to BoT-SORT |
| Backend | Python 3.11, FastAPI, OpenCV, Pydantic |
| Frontend | React, Vite |
| Testing | pytest (unit + integration) |

## Architecture

```text
React Frontend --HTTP--> FastAPI Backend --> Services --> YOLO26n + ByteTrack
```

Full breakdown (layering, request lifecycle, singleton vs. per-request
state, known limitations): **`docs/architecture.md`**.

## Installation

```bash
git clone <this repo>
cd visiontrack-ai

cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

cd ../frontend
npm install
```text

## Usage

```bash
# terminal 1 -- backend
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2 -- frontend
cd frontend && npm run dev
```

Open <http://localhost:5173>, upload an image or video, and run
detection or tracking. Or hit the API directly:

```bash
curl -F "file=@sample.jpg" http://localhost:8000/detect/image
curl -F "file=@sample.mp4" http://localhost:8000/track/video
```text

Run the test suite: `cd backend && pytest`.

## API

Full endpoint reference, request/response shapes, and error codes:
**`docs/api.md`**.

## Detection

Pretrained YOLO26n, loaded once per process. A `Detection` is one
bounding box in one frame -- no memory of any other frame. Full
writeup, including a known nuance with YOLO26's NMS-free head:
**`docs/detection.md`**.

## Tracking

Ultralytics' built-in ByteTrack (via `model.track(persist=True)`)
assigns persistent IDs across frames -- a `Track` *is* a `Detection`
plus one more fact: which real object this is, across time. Track IDs
are temporary and session-scoped (see **Privacy**, below). Full
writeup, including how tracker state is reset between videos and the
BoT-SORT upgrade path: **`docs/tracking.md`**.

## Counting

A configurable virtual line (stored as a ratio of frame size, so it
works at any resolution). An object's center must genuinely cross the
line -- true segment intersection, not just "did the side flip" -- to
count as an entry or exit, and each tracked object is counted at most
once per video to prevent jitter near the line from double-counting.
Full writeup, including that deliberate simplification and its
tradeoffs: **`docs/counting.md`**.

## Evaluation

Detection (mAP@50, mAP@50:95), tracking (ID switches, fragmentation,
identity consistency), and counting-accuracy metrics all have working,
**unit-tested** implementations (`backend/evaluation/metrics_*.py`) and
a CLI harness (`backend/evaluation/evaluate.py`) to run them against
real media. **No real evaluation numbers exist yet** -- this project
was built without network access to install the ML stack or record
real test footage. That's stated plainly rather than papered over with
invented numbers. Full status and how to actually get numbers:
**`docs/evaluation.md`**.

## Deployment

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend at <http://localhost>, API at <http://localhost:8000>.
Full details, environment variables, and a production checklist
(what's *not* safe to scale yet, and why): **`docs/deployment.md`**.

## Limitations

- **No real evaluation has been run** -- see above.
- **Synchronous processing only** -- a video request blocks until
  that video finishes; no background job queue yet (though
  `GET /results/{id}` is already shaped for one -- see
  `docs/architecture.md`).
- **In-memory results store** -- results are lost on restart and don't
  work across multiple worker processes.
- **Tracker state reset is unverified** -- `Tracker.reset()` reaches
  into an Ultralytics internal attribute defensively; hasn't been
  checked against a real install (no network during development).
- **Counting counts each object once per video** -- a genuinely
  repeated crossing by the same object won't be re-counted (see
  `docs/counting.md`).
- **No authentication** -- out of scope for this project.
- **No frontend automated tests yet.**
- **No real sample test media** -- `sample_data/` is currently empty.

## Future work

- Custom-trained model for a specific deployment scenario
- BoT-SORT for moving-camera footage, plus a real ByteTrack-vs-BoT-SORT
  comparison
- Traffic-specific analytics (cars/hour, density), heatmaps, speed
  estimation, region-of-interest zones
- Real-time webcam dashboard, cloud deployment, model export
  (ONNX/TensorRT)
- Background job queue + real result polling in the frontend

## Privacy

This is an object-*tracking* system, not a facial-identification
system. Track IDs (e.g. "Person #17") are temporary, session-scoped
labels -- never real-world identities. No face recognition or
biometric identification is implemented anywhere in this project.

## Phases

1. **Foundation** -- repo layout, config, health/config routes
2. **Image detection** -- YOLO26n, `/detect/image`
3. **Video detection** -- frame-by-frame, `/detect/video`
4. **ByteTrack integration** -- persistent IDs, `/track/video`
5. **Track IDs & trajectories** -- bounded per-track position history
6. **Counting line** -- entry/exit detection, no double-counting
7. **Analytics** -- dedicated accumulator service
8. **FastAPI** -- `/results/{id}`, global error handling, `result_id`
9. **React frontend** -- upload -> process -> results dashboard
10. **Testing** -- integration tests (real HTTP layer, ML calls stubbed via dependency_overrides), pytest config
11. **Evaluation** -- detection (mAP), tracking (ID switches/fragmentation), counting-accuracy metrics; `evaluate.py` CLI harness; honest "no real numbers yet" status
12. **Documentation** -- this README + `docs/architecture.md`, `detection.md`, `tracking.md`, `counting.md`, `evaluation.md`, `api.md`
13. **Deployment prep** -- Dockerfiles, docker-compose, nginx reverse proxy, CI, `docs/deployment.md` -- plus a real bug fixed along the way (model weights weren't landing in the persisted volume)

See `backend/README.md` and `frontend/README.md` for per-service setup.
