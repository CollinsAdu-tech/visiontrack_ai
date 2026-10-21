from app.utils.geometry import crossing_direction, has_crossed_line, side_of_point

# Horizontal counting line across y=100, from x=0 to x=200.
LINE_START = (0.0, 100.0)
LINE_END = (200.0, 100.0)


def test_point_above_line_is_negative_or_positive_consistently():
    above = side_of_point((100.0, 50.0), LINE_START, LINE_END)
    below = side_of_point((100.0, 150.0), LINE_START, LINE_END)
    # Whatever the sign convention, above and below must differ in sign.
    assert (above > 0) != (below > 0)


def test_point_exactly_on_line_is_zero():
    on_line = side_of_point((100.0, 100.0), LINE_START, LINE_END)
    assert on_line == 0


def test_movement_that_crosses_the_line_is_detected():
    prev_point = (100.0, 50.0)   # above
    curr_point = (100.0, 150.0)  # below
    assert has_crossed_line(prev_point, curr_point, LINE_START, LINE_END) is True


def test_movement_that_does_not_cross_the_line_is_not_detected():
    prev_point = (100.0, 20.0)
    curr_point = (100.0, 50.0)  # still above the line -- no crossing
    assert has_crossed_line(prev_point, curr_point, LINE_START, LINE_END) is False


def test_movement_outside_the_line_segment_span_does_not_count():
    # Both points are on opposite sides of y=100, but far outside x=[0, 200] --
    # a true (finite) segment intersection should reject this.
    prev_point = (500.0, 50.0)
    curr_point = (500.0, 150.0)
    assert has_crossed_line(prev_point, curr_point, LINE_START, LINE_END) is False


def test_crossing_direction_is_opposite_for_opposite_movements():
    down = crossing_direction((100.0, 50.0), (100.0, 150.0), LINE_START, LINE_END)
    up = crossing_direction((100.0, 150.0), (100.0, 50.0), LINE_START, LINE_END)
    assert down != 0
    assert up != 0
    assert down == -up
