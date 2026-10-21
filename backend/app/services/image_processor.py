"""
Image processing pipeline: decode -> detect -> annotate -> save -> summarize.

This is the one place that wires the detector, annotation, and file I/O
together for the image flow, so the route itself stays a thin HTTP
adapter with no OpenCV or Ultralytics calls of its own.
"""

from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.detection import Detection
from app.services.annotation import annotate_image
from app.utils.files import safe_output_filename

logger = get_logger(__name__)


class ImageProcessingResult:
    def __init__(
        self,
        detections: list[Detection],
        object_counts: dict[str, int],
        output_path: Path,
    ):
        self.detections = detections
        self.object_counts = object_counts
        self.output_path = output_path


def process_image(image_bytes: bytes, original_ext: str, detector) -> ImageProcessingResult:
    """
    `detector` just needs a `.predict(image) -> list[Detection]` method --
    duck-typed on purpose so tests can inject a stub without loading YOLO.
    """
    settings = get_settings()

    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image -- the file may be corrupt.")

    detections = detector.predict(image)
    annotated = annotate_image(image, detections)
    object_counts = dict(Counter(d.class_name for d in detections))

    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / safe_output_filename(original_ext)
    cv2.imwrite(str(output_path), annotated)

    logger.info("Processed image: %d detection(s) -> %s", len(detections), output_path)

    return ImageProcessingResult(
        detections=detections,
        object_counts=object_counts,
        output_path=output_path,
    )
