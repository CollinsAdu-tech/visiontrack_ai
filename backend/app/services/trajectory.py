"""
TrajectoryStore -- maintains a bounded history of center points per
track ID, plus first/last-seen frame numbers.

This is application-level state, separate from Ultralytics' own tracker
state (see Tracker.reset() in services/tracker.py). It's intentionally
NOT a singleton: one TrajectoryStore is created per video-processing
call (see video_processor.process_tracked_video), so trajectories never
leak between unrelated videos the way a shared object could.

History length is bounded (TRAJECTORY_LENGTH, default 30) so a track
that survives thousands of frames doesn't grow its history forever --
see spec section 14/"Object trajectory".
"""

from collections import deque


class TrajectoryStore:
    def __init__(self, max_length: int):
        self.max_length = max_length
        self._trajectories: dict[int, deque] = {}
        self._first_seen_frame: dict[int, int] = {}
        self._last_seen_frame: dict[int, int] = {}

    def update(self, track_id: int, center: tuple[float, float], frame_index: int) -> tuple[float, float] | None:
        """
        Record a new center point for this track at this frame.
        Returns the *previous* center point (before this update), or
        None if this is the first time we've seen this track -- useful
        for Phase 6's line-crossing test, which needs a "before" and
        "after" point.
        """
        trajectory = self._trajectories.setdefault(track_id, deque(maxlen=self.max_length))
        previous_center = trajectory[-1] if trajectory else None

        trajectory.append(center)
        self._first_seen_frame.setdefault(track_id, frame_index)
        self._last_seen_frame[track_id] = frame_index

        return previous_center

    def get_trajectory(self, track_id: int) -> list[tuple[float, float]]:
        return list(self._trajectories.get(track_id, ()))

    def first_seen_frame(self, track_id: int) -> int | None:
        return self._first_seen_frame.get(track_id)

    def last_seen_frame(self, track_id: int) -> int | None:
        return self._last_seen_frame.get(track_id)

    def known_track_ids(self) -> list[int]:
        return list(self._trajectories.keys())
