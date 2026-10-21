"""
Analytics service -- accumulates per-frame stats into a final summary.

Pulled out of video_processor.py so "what do we track and how do we
summarize it" is its own testable unit, independent of any real video
I/O, OpenCV, or ML calls. video_processor.py just calls record_frame()
once per frame and finalize() once at the end.
"""

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class VideoAnalytics:
    frames_processed: int = 0
    source_fps: float = 0.0
    duration_seconds: float = 0.0
    processing_seconds: float = 0.0
    processing_fps: float = 0.0
    object_counts: dict[str, int] = field(default_factory=dict)
    current_objects: int = 0          # objects visible in the last processed frame
    unique_tracked_objects: int = 0   # only meaningful when tracking (vs. plain detection)
    entries: int = 0                  # only populated when counting is enabled
    exits: int = 0


class AnalyticsAccumulator:
    """
    Call record_frame() once per processed frame, then finalize() once
    at the end to get a VideoAnalytics summary.
    """

    def __init__(self):
        self._class_counts: Counter[str] = Counter()
        self._seen_track_ids: set[int] = set()
        self._current_objects = 0
        self._frames_processed = 0

    @property
    def frames_processed(self) -> int:
        return self._frames_processed

    def record_frame(self, class_names, track_ids: list[int] | None = None) -> None:
        """
        `class_names`: the class name of every object visible this frame
        (plain detections or tracks, whichever pipeline is running).
        `track_ids`: pass this only when tracking -- lets us tell "12
        detections this frame" apart from "12 *unique* objects total".
        """
        names = list(class_names)
        self._class_counts.update(names)
        self._current_objects = len(names)
        if track_ids is not None:
            self._seen_track_ids.update(track_ids)
        self._frames_processed += 1

    def finalize(self, source_fps: float, elapsed_seconds: float, entries: int = 0, exits: int = 0) -> VideoAnalytics:
        return VideoAnalytics(
            frames_processed=self._frames_processed,
            source_fps=round(source_fps, 2),
            duration_seconds=round(self._frames_processed / source_fps, 2) if source_fps else 0.0,
            processing_seconds=round(elapsed_seconds, 2),
            processing_fps=round(self._frames_processed / elapsed_seconds, 2) if elapsed_seconds > 0 else 0.0,
            object_counts=dict(self._class_counts),
            current_objects=self._current_objects,
            unique_tracked_objects=len(self._seen_track_ids),
            entries=entries,
            exits=exits,
        )
