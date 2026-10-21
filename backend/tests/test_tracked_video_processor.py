"""
Uses a stub tracker (duck-typed on .reset() and .track(frame)) plus a
tiny synthetic video, so this test needs no YOLO/ByteTrack weights.
"""

import cv2
import numpy as np

from app.models.tracking import Track
from app.services.video_processor import process_tracked_video

_WIDTH, _HEIGHT, _FPS, _FRAME_COUNT = 64, 48, 10.0, 5


class StubTracker:
    def __init__(self, tracks_per_frame: list[list[Track]]):
        self._tracks_per_frame = tracks_per_frame
        self._i = 0
        self.reset_calls = 0

    def reset(self) -> None:
        self.reset_calls += 1
        self._i = 0

    def track(self, frame: np.ndarray) -> list[Track]:
        tracks = self._tracks_per_frame[self._i % len(self._tracks_per_frame)]
        self._i += 1
        return tracks


def _fake_mp4_bytes(tmp_path) -> bytes:
    path = tmp_path / "source.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, _FPS, (_WIDTH, _HEIGHT))
    frame = np.zeros((_HEIGHT, _WIDTH, 3), dtype=np.uint8)
    for _ in range(_FRAME_COUNT):
        writer.write(frame)
    writer.release()
    return path.read_bytes()


def test_process_tracked_video_counts_unique_ids(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    # Same two IDs (1, 2) reappear every frame -- should count as 2 unique
    # objects total, not 2 * frame_count.
    per_frame_tracks = [
        [
            Track(track_id=1, class_id=0, class_name="person", confidence=0.9, x1=1, y1=1, x2=10, y2=20),
            Track(track_id=2, class_id=0, class_name="person", confidence=0.8, x1=20, y1=1, x2=30, y2=20),
        ]
    ]
    tracker = StubTracker(per_frame_tracks)

    result = process_tracked_video(_fake_mp4_bytes(tmp_path), ".mp4", tracker)

    assert tracker.reset_calls == 1
    assert result.output_path.exists()
    assert result.analytics.frames_processed == _FRAME_COUNT
    assert result.analytics.unique_tracked_objects == 2
    assert result.analytics.object_counts == {"person": 2 * _FRAME_COUNT}

    config.get_settings.cache_clear()


def test_process_tracked_video_calls_reset_before_processing(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    tracker = StubTracker([[]])
    process_tracked_video(_fake_mp4_bytes(tmp_path), ".mp4", tracker)

    assert tracker.reset_calls == 1, "reset() must run before a new video is tracked"

    config.get_settings.cache_clear()


def _moving_track(track_id: int, center_x: float) -> Track:
    # y range [19, 29] keeps center_y=24, safely inside the default vertical
    # line's y span (0..frame height) so a horizontal crossing actually
    # intersects it.
    return Track(
        track_id=track_id, class_id=0, class_name="person", confidence=0.9,
        x1=center_x - 5, y1=19, x2=center_x + 5, y2=29,
    )


def test_process_tracked_video_counts_a_crossing_of_the_default_line(tmp_path, monkeypatch):
    """
    Default counting line is vertical at x = 0.5 * frame width = 32
    (frame is 64x48). A track moving from x=10 through x=34 crosses it.
    """
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    per_frame_tracks = [
        [_moving_track(1, 10)],
        [_moving_track(1, 16)],
        [_moving_track(1, 22)],  # still left of x=32
        [_moving_track(1, 28)],
        [_moving_track(1, 34)],  # now right of x=32 -- crossing happens here
    ]
    tracker = StubTracker(per_frame_tracks)

    result = process_tracked_video(_fake_mp4_bytes(tmp_path), ".mp4", tracker, counting_enabled=True)

    assert result.analytics.entries + result.analytics.exits == 1


def test_process_tracked_video_skips_counting_when_disabled(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    per_frame_tracks = [
        [_moving_track(1, 10)],
        [_moving_track(1, 16)],
        [_moving_track(1, 22)],
        [_moving_track(1, 28)],
        [_moving_track(1, 34)],
    ]
    tracker = StubTracker(per_frame_tracks)

    result = process_tracked_video(_fake_mp4_bytes(tmp_path), ".mp4", tracker, counting_enabled=False)

    assert result.analytics.entries == 0
    assert result.analytics.exits == 0

    config.get_settings.cache_clear()
