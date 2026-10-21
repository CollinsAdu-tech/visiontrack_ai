"""
Detector service -- loads YOLO26n once and exposes a clean predict().

The rest of the app should depend on `get_detector()` rather than
importing `ultralytics.YOLO` directly anywhere else. That keeps the ML
framework choice isolated to this one file.

`get_yolo_model()` is the actual weight-loading singleton; both this
module's Detector (predict-only) and services/tracker.py's Tracker
(predict+track) share the exact same loaded model rather than each
loading yolo26n.pt into memory separately.

Note on YOLO26: its default head is end-to-end / NMS-free (it outputs
up to 300 detections directly rather than running classic NMS). We keep
`iou_threshold` in config and pass it through, but it may have little
or no effect with the default head -- worth re-checking against the
Ultralytics docs if detection counts look off during Phase 2 testing.
"""

from functools import lru_cache

import numpy as np
from ultralytics import YOLO

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.detection import Detection

logger = get_logger(__name__)


@lru_cache
def get_yolo_model() -> YOLO:
    """
    Process-wide singleton for the raw Ultralytics model. Loads once.

    settings.model_name is a path (e.g. "models/yolo26n.pt"), not a
    bare filename -- see core/config.py for why. Ultralytics is
    expected to create that directory and download the weights there
    if the file doesn't exist yet (standard behavior across recent
    YOLO versions), but this hasn't been confirmed against a real
    install in this environment (no network during development) --
    worth checking on first real deploy that the file actually lands
    in models/ and not somewhere else.
    """
    settings = get_settings()
    logger.info("Loading detection model: %s", settings.model_name)
    model = YOLO(settings.model_name)
    logger.info("Model loaded. Classes available: %d", len(model.names))
    return model


class Detector:
    def __init__(self, model: YOLO, confidence: float, iou: float, image_size: int):
        self._model = model
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size

    def predict(self, image: np.ndarray) -> list[Detection]:
        """
        Run detection on a single image (BGR numpy array, as OpenCV loads it).
        Returns application-level Detection objects.
        """
        results = self._model.predict(
            source=image,
            conf=self.confidence,
            iou=self.iou,
            imgsz=self.image_size,
            verbose=False,
        )
        result = results[0]

        detections: list[Detection] = []
        if result.boxes is None:
            return detections

        for box in result.boxes:
            class_id = int(box.cls[0])
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=self._model.names[class_id],
                    confidence=float(box.conf[0]),
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )
        return detections


@lru_cache
def get_detector() -> Detector:
    """
    Process-wide singleton Detector.

    lru_cache means the model loads exactly once per process (on first
    call), no matter how many requests come in. FastAPI's dependency
    injection calls this on every request, but lru_cache short-circuits
    after the first real load.
    """
    settings = get_settings()
    return Detector(
        model=get_yolo_model(),
        confidence=settings.detection_confidence,
        iou=settings.iou_threshold,
        image_size=settings.image_size,
    )
