"""
Uses a stub detector (same contract as the image tests) plus a tiny
synthetic video written with cv2.VideoWriter, so this test needs no
YOLO weights and no real footage.
"""

import cv2
import numpy as np

from app.models.detection import Detection
from app.services.video_processor import process_video

_WIDTH, _HEIGHT, _FPS, _FRAME_COUNT = 64, 48, 10.0, 5


class StubDetector:
    def __init__(self, detections: list[Detection]):
        self._detections = detections

    def predict(self, frame: np.ndarray) -> list[Detection]:
        return self._detections


def _fake_mp4_bytes(tmp_path) -> bytes:
    path = tmp_path / "source.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, _FPS, (_WIDTH, _HEIGHT))
    frame = np.zeros((_HEIGHT, _WIDTH, 3), dtype=np.uint8)
    for _ in range(_FRAME_COUNT):
        writer.write(frame)
    writer.release()
    return path.read_bytes()


def test_process_video_reports_frame_count_and_counts(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    detections = [
        Detection(class_id=0, class_name="person", confidence=0.9, x1=1, y1=1, x2=10, y2=20),
    ]
    detector = StubDetector(detections)

    result = process_video(_fake_mp4_bytes(tmp_path), ".mp4", detector)

    assert result.output_path.exists()
    assert result.analytics.frames_processed == _FRAME_COUNT
    assert result.analytics.object_counts == {"person": _FRAME_COUNT}
    assert result.analytics.source_fps == _FPS

    config.get_settings.cache_clear()


def test_process_video_cleans_up_temp_upload(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    config.get_settings.cache_clear()

    process_video(_fake_mp4_bytes(tmp_path), ".mp4", StubDetector([]))

    # The temp input file should not remain after processing (privacy policy).
    leftover = list(upload_dir.glob("*.mp4")) if upload_dir.exists() else []
    assert leftover == []

    config.get_settings.cache_clear()


def test_process_video_raises_on_corrupt_file(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    config.get_settings.cache_clear()

    try:
        process_video(b"not-a-real-video", ".mp4", StubDetector([]))
        assert False, "expected ValueError for corrupt/unopenable video"
    except ValueError:
        pass

    config.get_settings.cache_clear()
