# Evaluation

## What's in here

- `metrics_detection.py` -- IoU, Average Precision, mAP@50, mAP@50:95.
  Pure stdlib, no dependencies. **Unit tested and actually executed**
  (not just syntax-checked) -- see `../tests/test_metrics_detection.py`.
- `metrics_tracking.py` -- ID switches, fragmentation, identity
  consistency. Same: pure stdlib, tested and executed.
- `metrics_counting.py` -- entry/exit counting accuracy against ground
  truth, following the spec's own worked example. Same: pure stdlib,
  tested and executed.
- `evaluate.py` -- the CLI harness that runs the **real** detector/
  tracker against a manifest of test media and writes a report. This
  one needs the full backend installed (Ultralytics, PyTorch, OpenCV,
  pydantic) because it does real inference -- it has NOT been run in
  this environment (no network access to install those, and no real
  test media exists yet -- see below).
- `manifest.example.json` -- the input schema `evaluate.py` expects.

## Running it

```bash
cd backend
pip install -r requirements.txt
python evaluation/evaluate.py --manifest evaluation/manifest.example.json
```

Writes a timestamped Markdown + JSON report to `evaluation/reports/`.

## Manifest schema

```json
{
  "images": [
    {
      "path": "relative/or/absolute/path.jpg",
      "ground_truth": [
        { "class_name": "person", "box": [x1, y1, x2, y2] }
      ]
    }
  ],
  "videos": [
    {
      "path": "relative/or/absolute/path.mp4",
      "ground_truth": { "entries": 10, "exits": 7 }
    }
  ]
}
```

`ground_truth` is optional on every entry. Omitting it still runs
detection/tracking and reports performance (FPS, inference time), but
the corresponding accuracy metric is reported as `null` with a note --
never estimated or invented.

## Honest status of this phase

**No real evaluation numbers exist yet**, because:

1. This environment has no network access, so the actual ML stack
   (PyTorch, Ultralytics) was never installable here to run inference.
2. `sample_data/images/` and `sample_data/videos/` (see spec section
   37) are empty -- there's no real or self-recorded test footage in
   this sandbox, and no labeled ground truth to evaluate against.

What *does* exist and was actually verified: the three metrics modules
are dependency-free, unit tested with hand-verifiable canonical cases
(a perfect detector scores AP=1.0, a detector that finds nothing
scores 0.0, the spec's own 10-entries/9-predicted counting example
computes to exactly 90% entry accuracy, etc.), and were **executed**
in this sandbox (not just syntax-checked) -- 22/22 passing.

To get real numbers: add labeled images/videos under `sample_data/`,
list them (with `ground_truth`) in a manifest, and run `evaluate.py`
in an environment with the full dependency stack installed. Do not
fill in placeholder numbers instead -- an honest "not yet measured"
is worth more than an invented benchmark.

## Not built in this phase

- Tracking-quality metrics (ID switches, fragmentation, identity
  consistency) aren't wired into `evaluate.py` yet -- they need
  per-frame ground-truth ID correspondences, which the current
  manifest schema doesn't capture. The metrics functions themselves
  are ready (`metrics_tracking.py`); only the manifest format and the
  harness glue are missing.
- The optional ByteTrack vs. BoT-SORT comparison (spec section 28).
