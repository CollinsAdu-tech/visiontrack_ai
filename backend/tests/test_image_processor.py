"""
Uses a stub detector so this test doesn't need to download/load the
actual YOLO26n weights (no network in CI/sandbox). process_image() only
requires an object with .predict(image) -> list[Detection], so this is
a legitimate substitute, not a workaround.
"""

import cv2
import numpy as np

from app.models.detection import Detection
from app.services.image_processor import process_image


class StubDetector:
    def __init__(self, detections: list[Detection]):
        self._detections = detections

    def predict(self, image: np.ndarray) -> list[Detection]:
        return self._detections


def _fake_jpeg_bytes() -> bytes:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    success, buffer = cv2.imencode(".jpg", image)
    assert success
    return buffer.tobytes()


def test_process_image_returns_detections_and_counts(tmp_path, monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    config.get_settings.cache_clear()

    detections = [
        Detection(class_id=0, class_name="person", confidence=0.9, x1=10, y1=10, x2=50, y2=90),
        Detection(class_id=0, class_name="person", confidence=0.8, x1=20, y1=15, x2=60, y2=95),
        Detection(class_id=2, class_name="car", confidence=0.7, x1=5, y1=5, x2=30, y2=30),
    ]
    detector = StubDetector(detections)

    result = process_image(_fake_jpeg_bytes(), ".jpg", detector)

    assert result.object_counts == {"person": 2, "car": 1}
    assert len(result.detections) == 3
    assert result.output_path.exists()

    config.get_settings.cache_clear()


def test_process_image_raises_on_corrupt_file(monkeypatch, tmp_path):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    config.get_settings.cache_clear()

    detector = StubDetector([])
    try:
        process_image(b"not-an-image", ".jpg", detector)
        assert False, "expected ValueError for corrupt image"
    except ValueError:
        pass

    config.get_settings.cache_clear()
