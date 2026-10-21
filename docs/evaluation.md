# Evaluation

VisionTrack AI's evaluation methodology, covering detection, tracking,
counting, and performance -- see `backend/evaluation/` for the actual
tooling this document describes.

## Methodology

| Concern    | Metric(s)                          | Where computed                         |
|------------|-------------------------------------|-----------------------------------------|
| Detection  | Precision, Recall, mAP@50, mAP@50:95 | `evaluation/metrics_detection.py`       |
| Tracking   | ID switches, fragmentation, identity consistency | `evaluation/metrics_tracking.py` |
| Counting   | Entry/exit accuracy vs. ground truth | `evaluation/metrics_counting.py`        |
| Performance| FPS, avg. inference time, total processing time | `AnalyticsAccumulator` + `evaluate.py` |

Detection AP follows the standard all-point-interpolation method
(PASCAL VOC 2012 / COCO-style): predictions are greedily matched to
ground truth by IoU, highest-confidence first, and AP is the area
under the resulting precision/recall envelope. mAP@50:95 averages AP
over IoU thresholds 0.50 through 0.95 in steps of 0.05, per class,
then across classes.

Tracking metrics are deliberately simplified versions of standard
MOT metrics (not full CLEAR-MOT/HOTA): ID switches count genuine
relabels of the same real object; fragmentation counts how many times
a tracked object is lost and re-found; identity consistency is the
fraction of frames where an object's ID agreed with its own majority
ID across the sequence.

Counting accuracy compares aggregate entry/exit totals against ground
truth (matching the spec's own worked example: ground truth 10
entries / 7 exits, system counted 9 / 7 -> 90% entry accuracy), not
individual timestamped crossing events.

## Current status: no real numbers yet

This is stated plainly rather than worked around: **no evaluation run
has produced real numbers**, because this project was built in a
sandboxed environment with no network access (so the ML dependencies
were never installable to run real inference) and no labeled test
media exists yet under `sample_data/`.

What *has* been verified: all three metrics modules are pure Python
with zero third-party dependencies, and their unit tests were actually
**executed** (not just syntax-checked) against hand-verifiable
canonical cases -- 22 out of 22 passing. That confirms the math is
correct; it says nothing about how well YOLO26n + ByteTrack actually
perform on real footage, which can only be measured by running them.

## How to get real numbers

1. Add labeled images/videos to `sample_data/images/` and
   `sample_data/videos/` (see spec section 37 for suggested
   coverage: single/multiple/crowded subjects, line-crossing,
   occlusion, varied lighting and camera angles).
2. Describe them, with ground truth, in a manifest JSON (see
   `backend/evaluation/manifest.example.json`).
3. In an environment with `pip install -r requirements.txt` run:

   ```bash
   python evaluation/evaluate.py --manifest your_manifest.json
   ```

4. A Markdown + JSON report is written to `evaluation/reports/`.

## Known evaluation gaps

- The pretrained model's own published benchmarks (from Ultralytics)
  are a different thing from *our* measured evaluation on our own
  test data, and this project has not conflated the two anywhere.
- Tracking-quality metrics need per-frame ground-truth ID
  correspondences the current manifest schema doesn't capture yet --
  the metric functions exist and are tested, but aren't wired into
  `evaluate.py`.
- No ByteTrack-vs-BoT-SORT comparison has been run (spec section 28,
  explicitly optional).
