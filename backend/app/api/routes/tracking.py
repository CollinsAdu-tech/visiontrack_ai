"""
POST /track/video

Thin HTTP layer only: validate the upload, delegate to the tracked-video
processing service, translate the result into the response schema.
Same pattern as api/routes/detection.py, kept in its own file because it
depends on the tracker rather than the plain detector.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.response import VideoDetectionResponse
from app.services.results_store import ResultsStore, get_results_store
from app.services.tracker import Tracker, get_tracker
from app.services.video_processor import process_tracked_video
from app.utils.files import FileTooLarge, UnsupportedFileType, validate_video_upload

router = APIRouter(tags=["tracking"])
logger = get_logger(__name__)


@router.post("/track/video", response_model=VideoDetectionResponse)
async def track_video(
    file: UploadFile = File(...),
    counting_enabled: bool | None = Form(default=None),
    tracker: Tracker = Depends(get_tracker),
    results_store: ResultsStore = Depends(get_results_store),
) -> VideoDetectionResponse:
    data = await file.read()

    try:
        validate_video_upload(file, data)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    ext = Path(file.filename or "").suffix.lower()
    if counting_enabled is None:
        counting_enabled = get_settings().counting_enabled_default

    try:
        result = process_tracked_video(data, ext, tracker, counting_enabled=counting_enabled)
    except ValueError as exc:
        # e.g. corrupt file, unsupported codec, unopenable video
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected failure during video tracking")
        raise HTTPException(status_code=500, detail="Video tracking failed.") from None

    output_url = f"/outputs/{result.output_path.name}"
    result_id = results_store.create(media_type="video", output_url=output_url, analytics=result.analytics.__dict__)

    return VideoDetectionResponse(
        success=True,
        output_url=output_url,
        analytics=result.analytics.__dict__,
        result_id=result_id,
    )
