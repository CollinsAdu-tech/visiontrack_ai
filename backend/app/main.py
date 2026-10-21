"""
VisionTrack AI -- FastAPI entrypoint.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import detection, health, results, tracking
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s starting up", settings.app_name, settings.app_version)
    logger.info(
        "config: model=%s tracker=%s conf=%s imgsz=%s",
        settings.model_name,
        settings.tracker,
        settings.detection_confidence,
        settings.image_size,
    )
    yield
    # Nothing to clean up on shutdown yet -- the loaded model and any
    # in-memory state (ResultsStore) simply go away with the process.


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Detect, track, and count objects in images and video.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(detection.router)
app.include_router(tracking.router)
app.include_router(results.router)

# Serve annotated results. Directory must exist before mounting.
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last line of defense: every route already catches its own expected
    failures and maps them to a clean HTTPException (see api/routes/*),
    but if something unanticipated slips through, this still guarantees
    the client never sees a raw Python traceback.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})
