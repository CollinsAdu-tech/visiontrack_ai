"""
VisionTrack AI evaluation harness.

    python evaluate.py --manifest manifest.example.json

Runs the REAL detector/tracker (via app.services.*) against the images
and videos listed in a manifest JSON file (see manifest.example.json
for the schema), computes detection/counting metrics wherever ground
truth was supplied, always measures performance (FPS, timing), and
writes a Markdown + JSON report under evaluation/reports/.

This script needs the full backend environment installed (Ultralytics,
PyTorch, OpenCV, pydantic -- see ../requirements.txt) because it runs
real inference, unlike the pure-stdlib metrics_*.py modules it imports,
which are tested independently of this.

Honesty rule, straight from the spec: if a manifest entry has no
ground truth, this script reports that metric as null / "not
evaluated" -- it never fabricates a number to fill the gap.
"""

import argparse
import json
import platform
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # noqa: E402

from evaluation.metrics_counting import evaluate_counting  # noqa: E402
from evaluation.metrics_detection import map_50_95, mean_average_precision  # noqa: E402


def _hardware_info() -> dict:
    info = {
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "python_version": platform.python_version(),
        "cuda_available": False,
        "cuda_device": None,
    }
    try:
        import torch

        info["cuda_available"] = torch.cuda.is_available()
        if info["cuda_available"]:
            info["cuda_device"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return info


def _evaluate_images(image_entries: list[dict], detector) -> dict:
    gt_by_class: dict = defaultdict(list)
    pred_by_class: dict = defaultdict(list)
    class_ids: set = set()

    per_image_results = []
    total_inference_seconds = 0.0
    images_with_ground_truth = 0

    for i, entry in enumerate(image_entries):
        image_id = entry.get("path", f"image_{i}")
        image = cv2.imread(entry["path"])
        if image is None:
            per_image_results.append({"path": entry["path"], "error": "could not read image"})
            continue

        start = time.monotonic()
        detections = detector.predict(image)
        total_inference_seconds += time.monotonic() - start

        for det in detections:
            class_ids.add(det.class_name)
            pred_by_class[det.class_name].append((image_id, (det.x1, det.y1, det.x2, det.y2), det.confidence))

        ground_truth = entry.get("ground_truth")
        if ground_truth:
            images_with_ground_truth += 1
            for gt in ground_truth:
                class_ids.add(gt["class_name"])
                gt_by_class[gt["class_name"]].append((image_id, tuple(gt["box"])))

        per_image_results.append({"path": entry["path"], "detections": len(detections)})

    result = {
        "images_evaluated": len(image_entries),
        "images_with_ground_truth": images_with_ground_truth,
        "avg_inference_seconds": (
            round(total_inference_seconds / len(image_entries), 4) if image_entries else None
        ),
        "per_image": per_image_results,
    }

    if images_with_ground_truth > 0:
        class_id_list = sorted(class_ids)
        result["map_50"] = round(mean_average_precision(gt_by_class, pred_by_class, class_id_list, 0.5), 4)
        result["map_50_95"] = round(map_50_95(gt_by_class, pred_by_class, class_id_list), 4)
    else:
        result["map_50"] = None
        result["map_50_95"] = None
        result["note"] = "No image had ground_truth boxes -- mAP not computed (see manifest schema)."

    return result


def _evaluate_videos(video_entries: list[dict], tracker) -> dict:
    from app.services.video_processor import process_tracked_video

    results = []
    for entry in video_entries:
        path = Path(entry["path"])
        if not path.exists():
            results.append({"path": str(path), "error": "file not found"})
            continue

        video_bytes = path.read_bytes()
        outcome = process_tracked_video(video_bytes, path.suffix, tracker, counting_enabled=True)
        a = outcome.analytics

        entry_result = {
            "path": str(path),
            "frames_processed": a.frames_processed,
            "processing_fps": a.processing_fps,
            "predicted_entries": a.entries,
            "predicted_exits": a.exits,
            "unique_tracked_objects": a.unique_tracked_objects,
        }

        ground_truth = entry.get("ground_truth")
        if ground_truth:
            counting = evaluate_counting(
                ground_truth_entries=ground_truth["entries"],
                predicted_entries=a.entries,
                ground_truth_exits=ground_truth["exits"],
                predicted_exits=a.exits,
            )
            entry_result["counting_accuracy"] = {
                "entry_accuracy": round(counting.entry_accuracy, 4),
                "exit_accuracy": round(counting.exit_accuracy, 4),
                "overall_accuracy": round(counting.overall_accuracy, 4),
                "entry_absolute_error": counting.entry_absolute_error,
                "exit_absolute_error": counting.exit_absolute_error,
            }
        else:
            entry_result["counting_accuracy"] = None
            entry_result["note"] = "No ground_truth entries/exits in manifest -- counting accuracy not computed."

        results.append(entry_result)

    return {"videos_evaluated": len(video_entries), "per_video": results}


def _write_markdown_report(report: dict, output_path: Path) -> None:
    lines = [
        "# VisionTrack AI -- Evaluation Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Configuration",
        "",
        f"- Model: `{report['config']['model_name']}`",
        f"- Tracker: `{report['config']['tracker']}`",
        f"- Detection confidence threshold: {report['config']['detection_confidence']}",
        f"- Image size: {report['config']['image_size']}",
        "",
        "## Hardware",
        "",
        f"- Platform: {report['hardware']['platform']}",
        f"- Processor: {report['hardware']['processor']}",
        f"- Python: {report['hardware']['python_version']}",
        f"- CUDA available: {report['hardware']['cuda_available']}"
        + (f" ({report['hardware']['cuda_device']})" if report["hardware"]["cuda_device"] else ""),
        "",
        "## Detection",
        "",
        f"- Images evaluated: {report['detection']['images_evaluated']}",
        f"- Images with ground truth: {report['detection']['images_with_ground_truth']}",
        f"- Average inference time: {report['detection']['avg_inference_seconds']} s/image",
        f"- mAP@50: {report['detection']['map_50']}",
        f"- mAP@50:95: {report['detection']['map_50_95']}",
    ]
    if report["detection"].get("note"):
        lines.append(f"- Note: {report['detection']['note']}")

    lines += ["", "## Tracking / Counting", ""]
    if report["tracking"]["videos_evaluated"] == 0:
        lines.append("No videos in manifest.")
    for video in report["tracking"]["per_video"]:
        lines.append(f"### {video['path']}")
        if "error" in video:
            lines.append(f"- Error: {video['error']}")
            continue
        lines.append(f"- Frames processed: {video['frames_processed']}")
        lines.append(f"- Processing speed: {video['processing_fps']} fps")
        lines.append(f"- Predicted entries/exits: {video['predicted_entries']} / {video['predicted_exits']}")
        if video["counting_accuracy"]:
            ca = video["counting_accuracy"]
            lines.append(
                f"- Counting accuracy: entries {ca['entry_accuracy']:.0%}, "
                f"exits {ca['exit_accuracy']:.0%}, overall {ca['overall_accuracy']:.0%}"
            )
        else:
            lines.append(f"- Counting accuracy: not evaluated ({video.get('note', 'no ground truth')})")
        lines.append("")

    lines += [
        "## Limitations",
        "",
        "- Detection mAP uses a from-scratch, dependency-free AP implementation "
        "(see evaluation/metrics_detection.py) -- cross-check against pycocotools "
        "for anything beyond an internship-level evaluation.",
        "- ID-switch / fragmentation / identity-consistency tracking metrics "
        "(evaluation/metrics_tracking.py) require per-frame ground-truth ID "
        "correspondences, which this manifest format does not yet capture -- "
        "not reported here.",
        "- Counting accuracy compares aggregate totals, not individual "
        "timestamped crossing events.",
        "- No numbers in this report are estimated or invented: every metric "
        "above either has a real value from a real run, or is null with a note "
        "explaining why.",
        "",
    ]

    output_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate VisionTrack AI against a manifest of test media.")
    parser.add_argument("--manifest", required=True, help="Path to a manifest JSON file.")
    parser.add_argument("--output-dir", default="evaluation/reports", help="Where to write the report.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())

    # Imported here, not at module level, so `pytest` can collect this
    # directory's pure metrics_*.py tests even without the ML stack installed.
    from app.core.config import get_settings
    from app.services.detector import get_detector
    from app.services.tracker import get_tracker

    settings = get_settings()
    detector = get_detector()
    tracker = get_tracker()

    detection_results = _evaluate_images(manifest.get("images", []), detector)
    tracking_results = _evaluate_videos(manifest.get("videos", []), tracker)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "model_name": settings.model_name,
            "tracker": settings.tracker,
            "detection_confidence": settings.detection_confidence,
            "image_size": settings.image_size,
        },
        "hardware": _hardware_info(),
        "detection": detection_results,
        "tracking": tracking_results,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"report_{timestamp}.json"
    md_path = output_dir / f"report_{timestamp}.md"

    json_path.write_text(json.dumps(report, indent=2))
    _write_markdown_report(report, md_path)

    print(f"Report written to {md_path} and {json_path}")


if __name__ == "__main__":
    main()
