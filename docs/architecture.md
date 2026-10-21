# Architecture

## Layering

```text
Routes (app/api/routes/*)
   |
Services (app/services/*)   <- all CV/ML/business logic lives here
   |
ML/CV engine (Ultralytics YOLO26n + ByteTrack, via services/detector.py & tracker.py)
   |
Analytics (services/analytics.py, counter.py, trajectory.py)
   |
Output (annotated image/video file + JSON response)
```

Routes are intentionally thin: parse the request, call one service
function, map known failure types to HTTP status codes, return the
response model. No OpenCV or Ultralytics call appears in a route file.
This separation is enforced by convention (there's no linter rule for
it), so it's worth checking on review.

## Request lifecycle

### Image: `POST /detect/image`

```text
Upload -> validate (extension, size) -> cv2.imdecode
   -> Detector.predict()          [services/detector.py]
   -> annotate_image()            [services/annotation.py]
   -> save output, register result [services/results_store.py]
   -> ImageDetectionResponse
```

### Video without tracking: `POST /detect/video`

Same shape as image, but frame-by-frame via `_video_io()` (a context
manager in `video_processor.py` that owns the temp-file write,
`cv2.VideoCapture`/`VideoWriter` lifecycle, and cleanup). No identity
persists between frames.

### Video with tracking: `POST /track/video`

```text
tracker.reset()                          -- fresh state for this video
for each frame:
    tracks = tracker.track(frame)        -- detection + ID assignment in one call
    trajectory_store.update(...)         -- bounded position history per track
    counter.update(...)                  -- entry/exit line-crossing check
    annotate_tracks() + draw_counting_line() + draw_count_event()
    accumulator.record_frame(...)
analytics = accumulator.finalize(...)
```

## Singletons vs. per-request state

Two different lifetimes are deliberately mixed here, and mixing them
up is the easiest way to introduce a bug:

- **Process-wide singletons** (`get_yolo_model()`, `get_detector()`,
  `get_tracker()`, all `@lru_cache`): the model weights load exactly
  once and are shared across every request, because reloading a
  network on every HTTP call would be far too slow.
- **Per-request state** (`TrajectoryStore`, `LineCounter`, and the
  tracker's *internal* ByteTrack buffer): must be fresh for every
  video, because trajectories and counts from one video must never
  leak into another. `TrajectoryStore`/`LineCounter` are plain objects
  created fresh each call, which is trivial. The tracker's internal
  state is trickier: it lives inside the shared, singleton
  `YOLO` model object, so `Tracker.reset()` must be called explicitly
  before each new video (see `services/tracker.py`) to clear it. This
  is flagged in that file's docstring as something to verify against
  the installed Ultralytics version, since the exact attribute path
  has moved across releases.

## Results storage

`services/results_store.py` is an in-memory, single-process dict.
Every processing call registers its result under a generated
`result_id`, which is what `GET /results/{result_id}` looks up. This
is explicitly a placeholder: it's lost on restart and doesn't work
across multiple worker processes. A real deployment would swap this
for a database or job queue -- and because every route already reads
and writes through this one interface, that swap wouldn't touch the
routes or response schemas at all.

## Frontend

React (Vite) SPA, calling the backend over `fetch`. `useVisionTrack.js`
is the single state machine (`idle -> uploading -> processing ->
completed/failed`) every component renders from -- no component holds
its own copy of that state. See `frontend/README.md` for the design
rationale.

## Known limitations

- No background job queue: a slow video upload blocks the HTTP
  request for its whole processing time. `GET /results/{id}` exists
  and is structured so swapping to async processing later is a
  service-layer change, not an API-shape change -- but that swap
  hasn't been done.
- `ResultsStore` is in-memory only (see above).
- No authentication/authorization anywhere -- out of scope per the
  spec (section 45).
