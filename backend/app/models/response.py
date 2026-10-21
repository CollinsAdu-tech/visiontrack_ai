from pydantic import BaseModel

from app.models.detection import Detection


class ImageDetectionResponse(BaseModel):
    success: bool
    media_type: str = "image"
    detections: list[Detection]
    object_counts: dict[str, int]
    output_url: str
    result_id: str


class VideoAnalyticsSchema(BaseModel):
    frames_processed: int
    source_fps: float
    duration_seconds: float
    processing_seconds: float
    processing_fps: float
    object_counts: dict[str, int]
    current_objects: int = 0
    unique_tracked_objects: int = 0
    entries: int = 0
    exits: int = 0


class VideoDetectionResponse(BaseModel):
    success: bool
    media_type: str = "video"
    output_url: str
    analytics: VideoAnalyticsSchema
    result_id: str


class ResultResponse(BaseModel):
    """GET /results/{result_id} -- re-fetch a previously processed result."""

    id: str
    status: str
    progress: int
    media_type: str
    output_url: str | None = None
    analytics: dict | None = None
    detections: list[Detection] | None = None
