# API Reference

Base URL in development: `http://localhost:8000`

## `GET /health`

```json
{ "status": "ok", "app_name": "VisionTrack AI", "version": "0.1.0" }
```

## `GET /config`

Safe, public configuration only -- no secrets, no file-system paths.

```json
{ "model": "yolo26n", "tracker": "bytetrack", "supported_modes": ["image", "video"] }
```

## `POST /detect/image`

Multipart upload. Field: `file` (`.jpg`/`.jpeg`/`.png`/`.bmp`, up to
`MAX_UPLOAD_SIZE_MB`).

```bash
curl -F "file=@sample.jpg" http://localhost:8000/detect/image
```

Response: see `docs/detection.md`.

## `POST /detect/video`

Multipart upload. Field: `file` (`.mp4`/`.mov`/`.avi`/`.mkv`).
Per-frame detection only -- **no persistent track IDs**. See
`POST /track/video` for tracking.

```bash
curl -F "file=@sample.mp4" http://localhost:8000/detect/video
```

## `POST /track/video`

Multipart upload. Fields:

- `file` (required) -- same video formats as above
- `counting_enabled` (optional, `true`/`false`) -- defaults to
  `COUNTING_ENABLED_DEFAULT` (`true`)

```bash
curl -F "file=@sample.mp4" -F "counting_enabled=true" http://localhost:8000/track/video
```

Response: see `docs/tracking.md`.

## `GET /results/{result_id}`

Re-fetch a previously processed result by the `result_id` returned
from any `/detect/*` or `/track/*` call.

```json
{
  "id": "a1b2c3d4e5f6",
  "status": "completed",
  "progress": 100,
  "media_type": "video",
  "output_url": "/outputs/<generated>.mp4",
  "analytics": { "...": "..." },
  "detections": null
}
```

All processing today is synchronous, so `status` is always
`"completed"` by the time a `result_id` exists -- see
`docs/architecture.md` for why the response shape is future-friendly
toward async processing anyway. `404` if the ID doesn't exist.

## `GET /outputs/{filename}`

Static file serving for annotated results. Not meant to be constructed
by hand -- always use the `output_url` a response gave you.

## Error responses

Every error is a clean JSON body, never a raw Python traceback:

```json
{ "detail": "human-readable message" }
```

| Status | Meaning |
|---|---|
| `404` | Unknown `result_id` |
| `413` | File exceeds `MAX_UPLOAD_SIZE_MB` |
| `415` | Unsupported file extension for that endpoint |
| `422` | Corrupt/undecodable file, or FastAPI's own request-shape validation (e.g. missing `file` field) |
| `500` | Unexpected server error (also caught by a global handler as defense-in-depth -- see `app/main.py`) |
