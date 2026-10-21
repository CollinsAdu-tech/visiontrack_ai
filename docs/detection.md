# Detection

## Model: YOLO26n

Pretrained `yolo26n.pt`, loaded once per process via
`services/detector.get_yolo_model()` and never retrained. The `n`
(nano) variant trades some accuracy for speed and low hardware
requirements -- the right tradeoff for demonstrating a complete
pipeline rather than chasing the best possible detector (see spec
section 5).

## Pipeline

```text
Input frame (BGR numpy array, as OpenCV loads it)
  -> model.predict(conf=DETECTION_CONFIDENCE, iou=IOU_THRESHOLD, imgsz=IMAGE_SIZE)
  -> Ultralytics Results.boxes (xyxy, conf, cls)
  -> app.models.detection.Detection (one per box)
```

`Detection` is deliberately decoupled from Ultralytics' own `Results`/
`Boxes` objects -- it's a plain typed shape (`class_id`, `class_name`,
`confidence`, `x1/y1/x2/y2`, plus computed `width`/`height`/`center_x`/
`center_y`). If the detection framework ever changes, only
`detector.py` needs to change; nothing downstream (annotation,
tracking, routes) touches Ultralytics types directly.

## Configuration

| Setting | Default | Notes |
|---|---|---|
| `MODEL_NAME` | `models/yolo26n.pt` | a path, not a bare filename -- see `docs/deployment.md` for why |
| `DETECTION_CONFIDENCE` | `0.25` | |
| `IOU_THRESHOLD` | `0.70` | see note below |
| `IMAGE_SIZE` | `640` | |

These are starting values, not verified-optimal ones (spec section
10) -- there's been no real evaluation run yet to tune them (see
`docs/evaluation.md`).

## Known nuance: YOLO26's NMS-free head

YOLO26's default head is end-to-end / NMS-free: it outputs up to 300
detections directly rather than running classic non-max suppression.
`IOU_THRESHOLD` is still wired through to `model.predict(iou=...)` for
flexibility, but it may have little or no effect with the default
head. This was flagged during Phase 1 (before any detection code was
written) and hasn't been re-verified against real inference output
since -- worth checking first if detection counts look off (e.g.
duplicate boxes on the same object) once this runs against real data.

## Response shape

`POST /detect/image` returns:

```json
{
  "success": true,
  "media_type": "image",
  "detections": [
    { "class_id": 0, "class_name": "person", "confidence": 0.91,
      "x1": 120, "y1": 80, "x2": 300, "y2": 500,
      "width": 180, "height": 420, "center_x": 210, "center_y": 290 }
  ],
  "object_counts": { "person": 1 },
  "output_url": "/outputs/<generated>.jpg",
  "result_id": "a1b2c3d4e5f6"
}
```text

See `docs/api.md` for the full endpoint reference.
