"""
LineCounter -- turns "this track's center moved from point A to point B"
into entry/exit counts, using the counting line.

Simplification (documented, not hidden): each track_id is counted AT
MOST ONCE for its lifetime, on its first confirmed crossing -- matching
the spec's own worked example (section 18: "Person #12 ... crosses ...
ENTRY recorded ... Person #12 remains counted"). This is a deliberate
MVP choice, not an oversight: it fully prevents jitter near the line
from causing repeated counts, at the cost of not re-counting an object
that genuinely walks back and forth across the line multiple times. A
future version could replace the one-time flag with a per-track cooldown
window to allow re-counting after N frames -- see docs/counting.md.

Like TrajectoryStore, this is NOT a singleton -- one LineCounter is
created per video so counts never carry over between videos.
"""

from app.utils.geometry import Point, crossing_direction, has_crossed_line


class LineCounter:
    def __init__(self, line_start: Point, line_end: Point):
        self.line_start = line_start
        self.line_end = line_end
        self.entries = 0
        self.exits = 0
        self._counted_track_ids: set[int] = set()

    def update(self, track_id: int, previous_center: Point | None, current_center: Point) -> str | None:
        """
        Call once per track per frame with its previous and current
        center point. Returns "entry", "exit", or None if nothing was
        counted this call (no previous point yet, no crossing, or this
        track was already counted once).
        """
        if previous_center is None:
            return None  # first sighting of this track -- nothing to compare against yet

        if track_id in self._counted_track_ids:
            return None  # already counted once this video -- see class docstring

        if not has_crossed_line(previous_center, current_center, self.line_start, self.line_end):
            return None

        direction = crossing_direction(previous_center, current_center, self.line_start, self.line_end)
        if direction == 0:
            return None

        self._counted_track_ids.add(track_id)
        if direction > 0:
            self.entries += 1
            return "entry"
        else:
            self.exits += 1
            return "exit"
