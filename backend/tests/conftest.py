"""
Shared fixtures for integration tests.

Integration tests exercise the real HTTP layer (FastAPI routing,
multipart parsing, Pydantic response validation) but swap out the
actual ML calls via FastAPI's dependency_overrides, using the same
duck-typed stub pattern as the unit tests (StubDetector/StubTracker) --
so these tests need no YOLO/ByteTrack weights and no network.
"""

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.detection import Detection
from app.models.tracking import Track
from app.services.detector import get_detector
from app.services.tracker import get_tracker


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    """Guarantee one test's stub never leaks into the next."""
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def tiny_jpg_bytes() -> bytes:
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    return buffer.tobytes()


@pytest.fixture
def make_mp4_bytes(tmp_path):
    """Factory: make_mp4_bytes(frame_count=5) -> bytes of a tiny synthetic .mp4"""

    def _make(frame_count: int = 5, width: int = 64, height: int = 48, fps: float = 10.0) -> bytes:
        path = tmp_path / "integration_source.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for _ in range(frame_count):
            writer.write(frame)
        writer.release()
        return path.read_bytes()

    return _make


class StubDetector:
    """Same contract as app.services.detector.Detector: .predict(frame) -> list[Detection]."""

    def __init__(self, detections: list[Detection] | None = None):
        self._detections = detections if detections is not None else [
            Detection(class_id=0, class_name="person", confidence=0.91, x1=5, y1=5, x2=20, y2=30)
        ]

    def predict(self, frame) -> list[Detection]:
        return self._detections


class StubTracker:
    """Same contract as app.services.tracker.Tracker: .reset() and .track(frame) -> list[Track]."""

    def __init__(self, tracks: list[Track] | None = None):
        self._tracks = tracks if tracks is not None else [
            Track(track_id=1, class_id=0, class_name="person", confidence=0.9, x1=5, y1=5, x2=20, y2=30)
        ]
        self.reset_calls = 0

    def reset(self) -> None:
        self.reset_calls += 1

    def track(self, frame) -> list[Track]:
        return self._tracks


@pytest.fixture
def stub_detector(client):
    detector = StubDetector()
    app.dependency_overrides[get_detector] = lambda: detector
    return detector


@pytest.fixture
def stub_tracker(client):
    tracker = StubTracker()
    app.dependency_overrides[get_tracker] = lambda: tracker
    return tracker
