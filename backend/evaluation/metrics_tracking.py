"""
Tracking evaluation metrics -- simplified, documented versions of
standard multi-object-tracking (MOT) metrics, not a full CLEAR-MOT/HOTA
implementation. Good enough to catch "the tracker keeps swapping IDs"
or "the tracker keeps losing and re-finding objects" during an
internship-level evaluation; for a rigorous benchmark, use py-motmetrics
against these same inputs.

Input shape: a sequence of frames, each frame a mapping of
    ground_truth_id -> predicted_track_id_or_None
(None means that ground-truth object had no matching prediction in
that frame). Building that per-frame correspondence -- matching
predicted boxes to ground-truth boxes by IoU -- is a separate, prior
step (see metrics_detection.iou); this module only reasons about the
resulting ID sequences.
"""

FrameCorrespondence = dict  # {gt_id: pred_id | None}


def id_switches(frames: list[FrameCorrespondence]) -> int:
    """
    Count how many times a ground-truth object's predicted ID changes
    from what it was the last time that object *had* a prediction
    (skipping over gaps where it had none -- a gap alone is
    fragmentation, not a switch; see fragmentation_count below).
    """
    last_known_id: dict = {}
    switches = 0

    for frame in frames:
        for gt_id, pred_id in frame.items():
            if pred_id is None:
                continue
            if gt_id in last_known_id and last_known_id[gt_id] != pred_id:
                switches += 1
            last_known_id[gt_id] = pred_id

    return switches


def fragmentation_count(frames: list[FrameCorrespondence]) -> int:
    """
    Count fragmentation events: how many times a tracked object goes
    from having a prediction to not having one and then, later, gets a
    prediction again. Concretely: (number of contiguous tracked
    segments - 1), summed across all ground-truth objects.
    """
    # First, collect each gt object's full sequence of pred_id-or-None
    # across all frames, in order.
    sequences: dict = {}
    all_gt_ids = {gt_id for frame in frames for gt_id in frame}
    for gt_id in all_gt_ids:
        sequences[gt_id] = [frame.get(gt_id) for frame in frames]

    total_fragmentations = 0
    for sequence in sequences.values():
        segments = 0
        previously_tracked = False
        for pred_id in sequence:
            tracked_now = pred_id is not None
            if tracked_now and not previously_tracked:
                segments += 1
            previously_tracked = tracked_now
        if segments > 0:
            total_fragmentations += segments - 1

    return total_fragmentations


def identity_consistency(frames: list[FrameCorrespondence]) -> float:
    """
    Fraction of (object, frame) pairs where the object's predicted ID
    matches that object's *majority* predicted ID across the whole
    sequence. 1.0 means every tracked frame agreed on one ID per
    object; lower means the tracker kept relabeling the same object.
    Micro-averaged across all ground-truth objects (not one object,
    one vote) so objects seen in more frames count proportionally more.
    """
    sequences: dict = {}
    all_gt_ids = {gt_id for frame in frames for gt_id in frame}
    for gt_id in all_gt_ids:
        sequences[gt_id] = [frame.get(gt_id) for frame in frames if frame.get(gt_id) is not None]

    total_predicted_frames = 0
    total_matching_frames = 0

    for pred_ids in sequences.values():
        if not pred_ids:
            continue
        counts: dict = {}
        for pid in pred_ids:
            counts[pid] = counts.get(pid, 0) + 1
        majority_id = max(counts, key=counts.get)

        total_predicted_frames += len(pred_ids)
        total_matching_frames += counts[majority_id]

    if total_predicted_frames == 0:
        return 0.0
    return total_matching_frames / total_predicted_frames
