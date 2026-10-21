# Tracking

## Detection vs. Track

This distinction matters and is enforced in the type system, not just
in prose (spec section 13):

- **Detection**: "there is a person here, 0.91 confidence" -- true for
  one frame, no memory of any other frame.
- **Track**: "this is Person #17, 0.91 confidence" -- the same real
  object, recognized as such across frames.

`app/models/tracking.py`'s `Track` is a subclass of `Detection` adding
exactly one field, `track_id`. It inherits `width`/`height`/`center_x`/
`center_y` for free.

A `track_id` is a **temporary, session-scoped label**, never a
real-world identity -- see the privacy note in the root README.

## How tracking actually works here

Unlike detection, Ultralytics does detection and tracking together in
a single call: `model.track(frame, persist=True, tracker="bytetrack.yaml")`.
There is no separate "take these Detections and associate them
frame-to-frame" step to write ourselves -- `services/tracker.py`'s
`Tracker.track(frame)` calls `model.track()` directly on the raw
frame, not `detector.predict()` followed by some association logic.

`persist=True` tells Ultralytics to keep its internal tracker state
across successive `.track()` calls -- that's what gives an object the
same ID from one frame to the next within a single video.

## Resetting between videos

The loaded model is a process-wide singleton (see
`docs/architecture.md`), but ByteTrack's internal state lives on that
same model object. Without an explicit reset, track IDs from a
previous, unrelated video could bleed into the next one.
`Tracker.reset()` clears this before each new video (called from
`video_processor.process_tracked_video()`), reaching into
`model.predictor.trackers` defensively -- logging a warning rather
than crashing if that attribute path doesn't exist in whatever
Ultralytics version is actually installed. **This has not been
verified against a real Ultralytics install** (no network access
during development) -- if track IDs look wrong across back-to-back
video uploads, this is the first place to check.

## Upgrade path: ByteTrack -> BoT-SORT

Swapping trackers is a one-line config change (`TRACKER=botsort.yaml`
instead of `bytetrack.yaml`), not a rewrite -- `Tracker` doesn't know
or care which tracker config string it's holding. Ultralytics
describes ByteTrack as the fast/simple baseline (no ReID, no
camera-motion compensation) and BoT-SORT as better suited to
moving-camera footage. No comparison between the two has been run
(spec section 28, explicitly optional) -- see `docs/evaluation.md`.

## Trajectories

`services/trajectory.py`'s `TrajectoryStore` keeps a bounded history
(`deque(maxlen=TRAJECTORY_LENGTH)`, default 30) of center points per
track ID. Like `LineCounter` (see `docs/counting.md`), it's created
fresh per video -- never a shared singleton -- so histories can't leak
between unrelated uploads. The annotated output video draws each
track's recent path as a thin colored line.

## Response shape

`POST /track/video` returns the same analytics shape as
`/detect/video`, plus tracking-specific fields:

```json
{
  "success": true,
  "media_type": "video",
  "output_url": "/outputs/<generated>.mp4",
  "result_id": "a1b2c3d4e5f6",
  "analytics": {
    "frames_processed": 1200,
    "current_objects": 3,
    "unique_tracked_objects": 17,
    "entries": 12,
    "exits": 7,
    "object_counts": { "person": 940, "car": 260 },
    "processing_fps": 18.4
  }
}
```

See `docs/api.md` for the full endpoint reference and
`docs/counting.md` for how `entries`/`exits` are computed.
