"""
Counting evaluation metrics.

Deliberate scope limit: this compares aggregate counts (total entries,
total exits over a whole video), not individual timestamped
crossing-events -- matching exactly how the spec's own worked example
frames it (section 35: "Ground truth: 10 entries, 7 exits. System: 9
entries, 7 exits."). It does not verify that the 9 counted entries were
the *same* 9 people the ground truth meant, only that the totals are
close. Event-level matching (aligning each predicted crossing to a
specific ground-truth crossing by timestamp) would be a meaningful
upgrade for a more rigorous evaluation, and isn't built here.
"""

from dataclasses import dataclass


@dataclass
class CountingAccuracy:
    ground_truth_entries: int
    predicted_entries: int
    entry_accuracy: float
    entry_absolute_error: int

    ground_truth_exits: int
    predicted_exits: int
    exit_accuracy: float
    exit_absolute_error: int

    overall_accuracy: float


def _single_direction_accuracy(ground_truth: int, predicted: int) -> float:
    if ground_truth == 0:
        # No real events to find -- perfect only if we also predicted zero.
        return 1.0 if predicted == 0 else 0.0
    correctly_counted = min(ground_truth, predicted)
    return correctly_counted / ground_truth


def evaluate_counting(
    ground_truth_entries: int,
    predicted_entries: int,
    ground_truth_exits: int,
    predicted_exits: int,
) -> CountingAccuracy:
    entry_accuracy = _single_direction_accuracy(ground_truth_entries, predicted_entries)
    exit_accuracy = _single_direction_accuracy(ground_truth_exits, predicted_exits)

    total_gt = ground_truth_entries + ground_truth_exits
    if total_gt == 0:
        overall = 1.0 if (predicted_entries == 0 and predicted_exits == 0) else 0.0
    else:
        correct_total = min(ground_truth_entries, predicted_entries) + min(ground_truth_exits, predicted_exits)
        overall = correct_total / total_gt

    return CountingAccuracy(
        ground_truth_entries=ground_truth_entries,
        predicted_entries=predicted_entries,
        entry_accuracy=entry_accuracy,
        entry_absolute_error=abs(predicted_entries - ground_truth_entries),
        ground_truth_exits=ground_truth_exits,
        predicted_exits=predicted_exits,
        exit_accuracy=exit_accuracy,
        exit_absolute_error=abs(predicted_exits - ground_truth_exits),
        overall_accuracy=overall,
    )
