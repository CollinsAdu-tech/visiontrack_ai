"""
Central configuration for VisionTrack AI.

All tunables live here (backed by environment variables) so that no
service or route hard-codes a magic number. Values are starting points,
not guaranteed-optimal settings -- see docs/detection.md once it exists.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App identity ---
    app_name: str = "VisionTrack AI"
    app_version: str = "0.1.0"

    # --- Model ---
    # Relative to the process's working directory (backend/ locally,
    # /app in the Docker image -- see backend/Dockerfile). Deliberately
    # NOT a bare filename: Ultralytics downloads a bare "yolo26n.pt" to
    # its own cache location, which the docker-compose "backend_models"
    # volume does NOT cover -- pointing at models/yolo26n.pt means the
    # weights land somewhere that volume actually persists, so they
    # survive container restarts instead of re-downloading every time.
    model_name: str = "models/yolo26n.pt"

    # --- Detection parameters ---
    detection_confidence: float = 0.25
    iou_threshold: float = 0.70
    image_size: int = 640

    # --- Tracking ---
    tracker: str = "bytetrack.yaml"
    trajectory_length: int = 30

    # --- Counting line ---
    # Expressed as (x_ratio, y_ratio) of frame width/height so the same
    # config works regardless of the uploaded video's resolution.
    # Default: a VERTICAL line down the middle of the frame -- the
    # right choice for footage where objects move left-right across
    # the frame (e.g. walking past a fixed camera). If your footage
    # instead shows objects moving toward/away from the camera
    # (up-down on screen), switch this back to a horizontal line:
    # (0.0, 0.5) -> (1.0, 0.5). The line only ever counts a crossing
    # when motion goes from one side of it to the other -- it must be
    # perpendicular to the actual direction of motion in your footage,
    # not just "somewhere objects pass through," or nothing will ever
    # register as a crossing (see docs/counting.md).
    counting_line_start_ratio: tuple[float, float] = (0.5, 0.0)
    counting_line_end_ratio: tuple[float, float] = (0.5, 1.0)
    counting_enabled_default: bool = True

    # --- Uploads / outputs ---
    max_upload_size_mb: int = 100
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    allowed_image_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp")
    allowed_video_extensions: tuple[str, ...] = (".mp4", ".mov", ".avi", ".mkv")

    # --- CORS ---
    cors_allow_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache means the .env file / environment is only parsed once
    per process, and every part of the app shares the same config object.
    """
    return Settings()
