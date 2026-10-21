from app.services.counter import LineCounter

LINE_START = (0.0, 100.0)
LINE_END = (200.0, 100.0)


def test_first_sighting_with_no_previous_point_counts_nothing():
    counter = LineCounter(LINE_START, LINE_END)
    event = counter.update(track_id=1, previous_center=None, current_center=(100.0, 50.0))
    assert event is None
    assert counter.entries == 0
    assert counter.exits == 0


def test_a_single_crossing_is_counted_once():
    counter = LineCounter(LINE_START, LINE_END)
    event = counter.update(track_id=1, previous_center=(100.0, 50.0), current_center=(100.0, 150.0))
    assert event in ("entry", "exit")
    assert counter.entries + counter.exits == 1


def test_same_object_cannot_be_counted_twice():
    counter = LineCounter(LINE_START, LINE_END)

    first_event = counter.update(track_id=7, previous_center=(100.0, 50.0), current_center=(100.0, 150.0))
    assert first_event is not None
    total_after_first = counter.entries + counter.exits

    # Same track crosses again (e.g. jitters back and forth near the line).
    second_event = counter.update(track_id=7, previous_center=(100.0, 150.0), current_center=(100.0, 50.0))
    assert second_event is None
    assert counter.entries + counter.exits == total_after_first


def test_opposite_direction_produces_the_opposite_event():
    down_counter = LineCounter(LINE_START, LINE_END)
    down_event = down_counter.update(track_id=1, previous_center=(100.0, 50.0), current_center=(100.0, 150.0))

    up_counter = LineCounter(LINE_START, LINE_END)
    up_event = up_counter.update(track_id=2, previous_center=(100.0, 150.0), current_center=(100.0, 50.0))

    assert down_event != up_event
    assert {down_event, up_event} == {"entry", "exit"}


def test_different_tracks_are_counted_independently():
    counter = LineCounter(LINE_START, LINE_END)
    counter.update(track_id=1, previous_center=(100.0, 50.0), current_center=(100.0, 150.0))
    counter.update(track_id=2, previous_center=(100.0, 50.0), current_center=(100.0, 150.0))
    assert counter.entries + counter.exits == 2


def test_no_crossing_counts_nothing():
    counter = LineCounter(LINE_START, LINE_END)
    event = counter.update(track_id=1, previous_center=(100.0, 20.0), current_center=(100.0, 50.0))
    assert event is None
    assert counter.entries == 0
    assert counter.exits == 0
