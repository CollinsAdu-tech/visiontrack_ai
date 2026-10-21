"""
Detection evaluation metrics: precision, recall, and Average Precision
(AP), following the standard "all-point interpolation" method used by
Pascal VOC 2012 / COCO (a monotone precision envelope integrated over
recall). This is a from-scratch, dependency-free implementation (pure
stdlib) so it can be tested without pydantic/ultralytics/numpy
installed -- see tests/test_metrics_detection.py.

Deliberate simplification, documented rather than hidden: this
implements the standard AP calculation faithfully, but doesn't
replicate every edge case of the official COCO API (e.g. "ignore"
regions, crowd annotations). For anything beyond an internship-level
evaluation, cross-check against pycocotools.

Terminology used throughout:
  gt_items:   list of (image_id, box) for ONE class
  pred_items: list of (image_id, box, confidence) for ONE class
  box:        (x1, y1, x2, y2)
"""

Box = tuple[float, float, float, float]


def iou(box_a: Box, box_b: Box) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


def average_precision(gt_items: list[tuple], pred_items: list[tuple], iou_threshold: float = 0.5) -> float:
    """
    AP for a single class at a single IoU threshold.

    Predictions are greedily matched to ground truth, highest confidence
    first: each prediction matches the highest-IoU *unmatched* ground
    truth box in the same image, if that IoU clears the threshold.
    Already-matched ground truth boxes can't be matched again (a second
    prediction on the same object counts as a false positive) --
    standard behavior, and why a detector that fires twice on one
    object doesn't get credit twice.
    """
    total_gt = len(gt_items)
    if total_gt == 0:
        return 0.0
    if len(pred_items) == 0:
        return 0.0

    # Group ground truth by image, tracking which boxes are already claimed.
    gt_by_image: dict = {}
    for image_id, box in gt_items:
        gt_by_image.setdefault(image_id, []).append({"box": box, "matched": False})

    ranked_preds = sorted(pred_items, key=lambda p: p[2], reverse=True)

    tp = [0] * len(ranked_preds)
    fp = [0] * len(ranked_preds)

    for i, (image_id, box, _confidence) in enumerate(ranked_preds):
        candidates = gt_by_image.get(image_id, [])
        best_iou = 0.0
        best_candidate = None
        for candidate in candidates:
            if candidate["matched"]:
                continue
            candidate_iou = iou(box, candidate["box"])
            if candidate_iou > best_iou:
                best_iou = candidate_iou
                best_candidate = candidate

        if best_candidate is not None and best_iou >= iou_threshold:
            best_candidate["matched"] = True
            tp[i] = 1
        else:
            fp[i] = 1

    cumulative_tp = 0
    cumulative_fp = 0
    precisions = []
    recalls = []
    for i in range(len(ranked_preds)):
        cumulative_tp += tp[i]
        cumulative_fp += fp[i]
        precisions.append(cumulative_tp / (cumulative_tp + cumulative_fp))
        recalls.append(cumulative_tp / total_gt)

    return _area_under_pr_curve(precisions, recalls)


def _area_under_pr_curve(precisions: list[float], recalls: list[float]) -> float:
    """
    All-point interpolation: replace the precision at each recall level
    with the maximum precision achieved at that recall level or any
    higher recall (a monotonically non-increasing "envelope"), then
    integrate that envelope over recall.
    """
    # Prepend the (recall=0, precision=1) anchor so the integration has
    # a clean start; the ranked-prediction loop already gives us the
    # natural end point (max recall reached).
    recalls = [0.0] + recalls
    precisions = [1.0] + precisions

    # Build the precision envelope from the right (monotonic non-increasing).
    envelope = precisions[:]
    for i in range(len(envelope) - 2, -1, -1):
        envelope[i] = max(envelope[i], envelope[i + 1])

    area = 0.0
    for i in range(1, len(recalls)):
        area += (recalls[i] - recalls[i - 1]) * envelope[i]
    return area


def mean_average_precision(
    gt_by_class: dict, pred_by_class: dict, class_ids: list, iou_threshold: float = 0.5
) -> float:
    """
    mAP at one IoU threshold: average AP across every class that has at
    least one ground truth instance. Classes with predictions but no
    ground truth are outside this metric's scope (nothing to recall).
    """
    aps = []
    for class_id in class_ids:
        gt_items = gt_by_class.get(class_id, [])
        if not gt_items:
            continue
        pred_items = pred_by_class.get(class_id, [])
        aps.append(average_precision(gt_items, pred_items, iou_threshold))
    return sum(aps) / len(aps) if aps else 0.0


def map_50_95(gt_by_class: dict, pred_by_class: dict, class_ids: list) -> float:
    """COCO-style mAP@50:95 -- mean of mAP at IoU thresholds 0.50, 0.55, ..., 0.95."""
    thresholds = [round(0.5 + 0.05 * i, 2) for i in range(10)]
    values = [mean_average_precision(gt_by_class, pred_by_class, class_ids, t) for t in thresholds]
    return sum(values) / len(values)
