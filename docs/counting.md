# Counting

## The virtual line

A configurable line an object's center must cross to count as an
entry or exit. Stored as **ratios** of frame width/height
(`COUNTING_LINE_START_RATIO`/`COUNTING_LINE_END_RATIO`, default a
**vertical** line down the middle: `(0.5, 0.0)` to `(0.5, 1.0)` -- the
right choice for footage where objects move left-right across the
frame), so one config works regardless of the uploaded video's actual
resolution -- `process_tracked_video()` converts the ratio to real
pixel coordinates using that video's own width/height before
processing.

The line must be roughly **perpendicular to the actual direction of
motion** in the footage, not just "somewhere objects happen to pass
through." A line that runs parallel to an object's motion will overlap
it in every frame without ever registering a crossing (their center
never moves from one side of it to the other) -- that looks like a
counting bug but is actually a placement mismatch. If your footage
shows motion toward/away from the camera instead of left-right, switch
back to a horizontal line: `(0.0, 0.5)` to `(1.0, 0.5)`.

## Geometry

`app/utils/geometry.py` answers two separate questions, kept as two
separate functions on purpose (easier to test in isolation):

1. **Which side of the line is this point on?** -- `side_of_point()`,
   a signed cross product (positive/negative/zero).
2. **Did the object's movement cross the line?** -- `has_crossed_line()`,
   a true finite **segment** intersection test (standard CCW
   orientation check), not just "did the side flip." This matters: an
   object moving far outside the line's actual on-screen span
   shouldn't count as crossing it just because its side relative to
   the line's infinite extension happened to change.

`crossing_direction()` then reports which way the crossing went (+1 or
-1), which `LineCounter` maps to "entry" or "exit."

## Counting and duplicate prevention

`app/services/counter.py`'s `LineCounter` increments `entries`/`exits`
only on a genuine, confirmed crossing -- and **counts each track ID at
most once for the entire video.** This is a deliberate simplification,
not an oversight, matching the spec's own worked example (section 18:
"Person #12 ... crosses ... ENTRY recorded ... Person #12 remains
counted"). It fully prevents jitter near the line from double-counting
an object that wobbles back and forth, at the documented cost of not
re-counting an object that genuinely walks back and forth across the
line multiple times in one video. A future version could replace the
one-time flag with a per-track cooldown window to allow re-counting
after some number of frames.

Like `TrajectoryStore`, `LineCounter` is created fresh per video --
never a shared singleton -- so counts from one video can never bleed
into the next.

## Enabling/disabling

`POST /track/video` accepts an optional `counting_enabled` form field
(defaults to `COUNTING_ENABLED_DEFAULT`, `true`). When disabled, no
`LineCounter` is created at all -- `entries`/`exits` are simply `0`,
and no line or event markers are drawn on the output video.

## Visualization

`services/annotation.py` draws:

- `draw_counting_line()` -- the line itself, labeled "COUNTING LINE"
- `draw_count_event()` -- a brief "ENTRY"/"EXIT" flash at the exact
  point and frame where a crossing was counted

## Evaluating counting accuracy

See `docs/evaluation.md` and `backend/evaluation/metrics_counting.py`
-- accuracy is measured against aggregate ground-truth entry/exit
totals, exactly as the spec's own example frames it (10 ground-truth
entries, 9 predicted -> 90% entry accuracy), not against individual
timestamped events.
