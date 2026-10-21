from evaluation.metrics_counting import evaluate_counting


def test_spec_worked_example():
    # spec section 35: ground truth 10 entries / 7 exits, system counted
    # 9 entries / 7 exits.
    result = evaluate_counting(
        ground_truth_entries=10, predicted_entries=9,
        ground_truth_exits=7, predicted_exits=7,
    )
    assert result.entry_accuracy == 0.9
    assert result.entry_absolute_error == 1
    assert result.exit_accuracy == 1.0
    assert result.exit_absolute_error == 0
    assert result.overall_accuracy == (9 + 7) / (10 + 7)


def test_perfect_counting_is_accuracy_one():
    result = evaluate_counting(
        ground_truth_entries=5, predicted_entries=5,
        ground_truth_exits=3, predicted_exits=3,
    )
    assert result.entry_accuracy == 1.0
    assert result.exit_accuracy == 1.0
    assert result.overall_accuracy == 1.0


def test_overcounting_is_capped_not_rewarded():
    # Predicting more than actually happened shouldn't inflate accuracy
    # past 1.0 for that direction.
    result = evaluate_counting(
        ground_truth_entries=5, predicted_entries=9,
        ground_truth_exits=0, predicted_exits=0,
    )
    assert result.entry_accuracy == 1.0
    assert result.entry_absolute_error == 4


def test_zero_ground_truth_events_with_zero_predicted_is_perfect():
    result = evaluate_counting(
        ground_truth_entries=0, predicted_entries=0,
        ground_truth_exits=0, predicted_exits=0,
    )
    assert result.entry_accuracy == 1.0
    assert result.exit_accuracy == 1.0
    assert result.overall_accuracy == 1.0


def test_zero_ground_truth_events_with_false_positive_predictions_is_zero():
    result = evaluate_counting(
        ground_truth_entries=0, predicted_entries=3,
        ground_truth_exits=0, predicted_exits=0,
    )
    assert result.entry_accuracy == 0.0
