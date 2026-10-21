"""
Geometry utilities for the counting line.

Two separate questions, kept as two separate functions on purpose
(easier to unit test each in isolation -- see spec section 38):
  1. Which side of the line is this point on?           -> side_of_point
  2. Did the object's movement cross the line segment?   -> has_crossed_line

A counting line is finite (a segment, not an infinite line), so we use
proper segment-intersection, not just "did the side change" -- an
object moving far outside the line's span shouldn't count as crossing
it just because its infinite-line side flipped.
"""

Point = tuple[float, float]


def side_of_point(point: Point, line_start: Point, line_end: Point) -> float:
    """
    Signed value indicating which side of the (infinite extension of the)
    line `point` is on: positive on one side, negative on the other,
    zero exactly on the line. This is the 2D cross product of
    (line_end - line_start) and (point - line_start).
    """
    x1, y1 = line_start
    x2, y2 = line_end
    px, py = point
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def _ccw(a: Point, b: Point, c: Point) -> bool:
    """True if a, b, c are in counter-clockwise order."""
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def has_crossed_line(prev_point: Point, curr_point: Point, line_start: Point, line_end: Point) -> bool:
    """
    True if the movement segment (prev_point -> curr_point) properly
    intersects the counting line segment (line_start -> line_end).

    Standard CCW-orientation segment-intersection test. Using true
    segment intersection (not just "did the infinite-line side change")
    means an object moving well outside the line's span doesn't
    spuriously count as a crossing.
    """
    a, b = line_start, line_end
    c, d = prev_point, curr_point
    return _ccw(a, c, d) != _ccw(b, c, d) and _ccw(a, b, c) != _ccw(a, b, d)


def crossing_direction(prev_point: Point, curr_point: Point, line_start: Point, line_end: Point) -> int:
    """
    Returns +1 if the point moved from the line's negative side to its
    positive side, -1 for the reverse, or 0 if no side change is
    detected (caller should typically only trust this after confirming
    has_crossed_line() is True).
    """
    prev_side = side_of_point(prev_point, line_start, line_end)
    curr_side = side_of_point(curr_point, line_start, line_end)
    if prev_side < 0 and curr_side > 0:
        return 1
    if prev_side > 0 and curr_side < 0:
        return -1
    return 0
