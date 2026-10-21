from evaluation.metrics_detection import (
    average_precision,
    iou,
    map_50_95,
    mean_average_precision,
)

PERFECT_BOX = (10.0, 10.0, 50.0, 50.0)
NO_OVERLAP_BOX = (200.0, 200.0, 240.0, 240.0)


def test_iou_of_identical_boxes_is_one():
    assert iou(PERFECT_BOX, PERFECT_BOX) == 1.0


def test_iou_of_non_overlapping_boxes_is_zero():
    assert iou(PERFECT_BOX, NO_OVERLAP_BOX) == 0.0


def test_iou_of_partial_overlap_is_between_zero_and_one():
    box_a = (0.0, 0.0, 10.0, 10.0)
    box_b = (5.0, 5.0, 15.0, 15.0)
    result = iou(box_a, box_b)
    assert 0.0 < result < 1.0


def test_perfect_detector_gets_ap_of_one():
    gt_items = [("img1", PERFECT_BOX)]
    pred_items = [("img1", PERFECT_BOX, 0.95)]
    assert average_precision(gt_items, pred_items, iou_threshold=0.5) == 1.0


def test_detector_that_finds_nothing_gets_ap_of_zero():
    gt_items = [("img1", PERFECT_BOX)]
    pred_items = []
    assert average_precision(gt_items, pred_items, iou_threshold=0.5) == 0.0


def test_no_ground_truth_gets_ap_of_zero_not_a_crash():
    assert average_precision([], [("img1", PERFECT_BOX, 0.9)], iou_threshold=0.5) == 0.0


def test_detector_that_finds_half_of_two_objects_gets_ap_of_half():
    # 2 GT boxes in one image, only one is ever detected -- max recall is
    # 0.5, precision stays 1.0 the whole way there, so AP == 0.5.
    gt_items = [("img1", PERFECT_BOX), ("img1", NO_OVERLAP_BOX)]
    pred_items = [("img1", PERFECT_BOX, 0.9)]
    assert average_precision(gt_items, pred_items, iou_threshold=0.5) == 0.5


def test_second_prediction_on_same_object_counts_as_false_positive():
    # Only one real object; two predictions both claim it. The second
    # can't also be a true positive (that would double-count the object).
    gt_items = [("img1", PERFECT_BOX)]
    pred_items = [("img1", PERFECT_BOX, 0.9), ("img1", PERFECT_BOX, 0.8)]
    ap = average_precision(gt_items, pred_items, iou_threshold=0.5)
    assert ap == 1.0  # recall already hit 1.0 before the redundant FP


def test_iou_threshold_rejects_low_overlap_matches():
    gt_items = [("img1", (0.0, 0.0, 10.0, 10.0))]
    # Overlaps a little, but not enough to count as a match at IoU 0.5.
    pred_items = [("img1", (8.0, 8.0, 18.0, 18.0), 0.9)]
    assert average_precision(gt_items, pred_items, iou_threshold=0.5) == 0.0


def test_mean_average_precision_averages_across_classes_with_ground_truth():
    gt_by_class = {
        "person": [("img1", PERFECT_BOX)],
        "car": [("img1", NO_OVERLAP_BOX)],
    }
    pred_by_class = {
        "person": [("img1", PERFECT_BOX, 0.9)],  # perfect -> AP 1.0
        "car": [],  # missed entirely -> AP 0.0
    }
    result = mean_average_precision(gt_by_class, pred_by_class, ["person", "car"], iou_threshold=0.5)
    assert result == 0.5


def test_map_50_95_is_between_zero_and_map_50_for_imperfect_detections():
    # A prediction offset just enough to fail some of the stricter IoU
    # thresholds in the 0.5:0.95 sweep, but still pass at 0.5.
    gt_items = [("img1", (0.0, 0.0, 100.0, 100.0))]
    pred_items = [("img1", (5.0, 5.0, 100.0, 100.0), 0.9)]
    gt_by_class = {"person": gt_items}
    pred_by_class = {"person": pred_items}

    map50 = mean_average_precision(gt_by_class, pred_by_class, ["person"], iou_threshold=0.5)
    map5095 = map_50_95(gt_by_class, pred_by_class, ["person"])

    assert 0.0 <= map5095 <= map50
