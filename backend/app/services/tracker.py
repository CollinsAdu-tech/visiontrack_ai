"""
Tracker service -- wraps Ultralytics' built-in tracking (ByteTrack by
default, BoT-SORT as a one-line config change) via `model.track(...)`.

Important difference from detector.py: Ultralytics does detection AND
tracking together in a single `model.track()` call -- there's no
separate "take these Detections and associate them" step to call
ourselves. So Tracker does NOT take pre-computed Detections as input;
it runs its own inference on the raw frame, same as Detector does, but
returns identity-carrying Tracks instead of plain Detections.

`persist=True` tells Ultralytics to keep track state across successive
`.track()` calls, which is what gives an object the same ID from one
frame to the next within one video. See core/config.py `tracker` for
swapping "bytetrack.yaml" -> "botsort.yaml" later (Phase 44 in the spec:
BoT-SORT for moving-camera footage).
"""

from functools import lru_cache

import numpy as np
from ultralytics import YOLO

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.tracking import Track
from app.services.detector import get_yolo_model

logger = get_logger(__name__)


class Tracker:
    def __init__(self, model: YOLO, tracker_config: str, confidence: float, iou: float, image_size: int):
        self._model = model
        self.tracker_config = tracker_config
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size

    def reset(self) -> None:
        """
        Clear tracker state before starting a new, independent video.

        Ultralytics keeps ByteTrack/BoT-SORT state on the model's
        predictor object, and our model instance is a process-wide
        singleton (shared across requests to avoid reloading weights).
        Without an explicit reset, track IDs from a previous video could
        continue into the next one.

        The exact attribute path (`model.predictor.trackers`) has moved
        across Ultralytics versions -- this is written defensively and
        logs a warning rather than crashing if it can't find a reset()
        method. Verify against the installed Ultralytics version; if
        track IDs look wrong across back-to-back video requests, this is
        the first place to check.
        """
        predictor = getattr(self._model, "predictor", None)
        trackers = getattr(predictor, "trackers", None) if predictor is not None else None
        if not trackers:
            return

        for single_tracker in trackers:
            reset_fn = getattr(single_tracker, "reset", None)
            if callable(reset_fn):
                reset_fn()
            else:
                logger.warning(
                    "Installed Ultralytics tracker has no reset() method; "
                    "track IDs may carry over from a previous video."
                )

    def track(self, frame: np.ndarray) -> list[Track]:
        """
        Run detection + tracking on a single frame (BGR numpy array).
        Call this once per frame, in order, with persist=True implied,
        for IDs to remain stable across the video. Call reset() first
        when starting a new, unrelated video.
        """
        results = self._model.track(
            source=frame,
            persist=True,
            tracker=self.tracker_config,
            conf=self.confidence,
            iou=self.iou,
            imgsz=self.image_size,
            verbose=False,
        )
        result = results[0]

        tracks: list[Track] = []
        if result.boxes is None or result.boxes.id is None:
            # No confirmed tracks in this frame yet -- normal on the very
            # first frame or when every detection is still unconfirmed.
            return tracks

        for box in result.boxes:
            if box.id is None:
                continue
            class_id = int(box.cls[0])
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            tracks.append(
                Track(
                    track_id=int(box.id[0]),
                    class_id=class_id,
                    class_name=self._model.names[class_id],
                    confidence=float(box.conf[0]),
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )
        return tracks


@lru_cache
def get_tracker() -> Tracker:
    """Process-wide singleton Tracker, sharing the same loaded weights as Detector."""
    settings = get_settings()
    return Tracker(
        model=get_yolo_model(),
        tracker_config=settings.tracker,
        confidence=settings.detection_confidence,
        iou=settings.iou_threshold,
        image_size=settings.image_size,
    )
