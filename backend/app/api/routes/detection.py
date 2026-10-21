"""
POST /detect/image
POST /detect/video

Thin HTTP layer only: validate the upload, delegate to the image/video
processing service, translate the result into the response schema.
No OpenCV/Ultralytics calls belong in this file.

/detect/video has no tracking yet (Phase 4 adds that as /track/video,
reusing this same video_processor pipeline with a tracker plugged in).
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.logging import get_logger
from app.models.response import ImageDetectionResponse, VideoDetectionResponse
from app.services.detector import Detector, get_detector
from app.services.image_processor import process_image
from app.services.results_store import ResultsStore, get_results_store
from app.services.video_processor import process_video
from app.utils.files import FileTooLarge, UnsupportedFileType, validate_image_upload, validate_video_upload

router = APIRouter(tags=["detection"])
logger = get_logger(__name__)


@router.post("/detect/image", response_model=ImageDetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    detector: Detector = Depends(get_detector),
    results_store: ResultsStore = Depends(get_results_store),
) -> ImageDetectionResponse:
    data = await file.read()

    try:
        validate_image_upload(file, data)
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    ext = Path(file.filename or "").suffix.lower()

    try:
        result = process_image(data, ext, detector)
    except ValueError as exc:
        # e.g. corrupt/undecodable image
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected failure during image detection")
        raise HTTPException(status_code=500, detail="Image processing failed.") from None

    output_url = f"/outputs/{result.output_path.name}"
    result_id = results_store.create(
        media_type="image",
        output_url=output_url,
        detections=[d.model_dump() for d in result.detections],
    )

    return ImageDetectionResponse(
        success=True,
        detections=result.detections,
        object_counts=result.object_counts,
        output_url=output_url,
        result_id=result_id,
    )


@router.post("/detect/video", response_model=VideoDetectionResponse)
async def detect_video(
    file: UploadFile = File(...),
    detector: Detector = Depends(get_detector),
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

    try:
        result = process_video(data, ext, detector)
    except ValueError as exc:
        # e.g. corrupt file, unsupported codec, unopenable video
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected failure during video detection")
        raise HTTPException(status_code=500, detail="Video processing failed.") from None

    output_url = f"/outputs/{result.output_path.name}"
    result_id = results_store.create(media_type="video", output_url=output_url, analytics=result.analytics.__dict__)

    return VideoDetectionResponse(
        success=True,
        output_url=output_url,
        analytics=result.analytics.__dict__,
        result_id=result_id,
    )
