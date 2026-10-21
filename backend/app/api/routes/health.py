"""
GET /health

The simplest possible endpoint: proves the FastAPI process is up and
config loads correctly, before any ML code is involved.
"""

from pathlib import Path

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/config")
def public_config() -> dict:
    """
    Return safe, public configuration only.

    Never expose secrets, file-system paths, or anything else that
    could aid an attacker here -- this endpoint is unauthenticated.
    """
    settings = get_settings()
    return {
        "model": Path(settings.model_name).stem,
        "tracker": settings.tracker.removesuffix(".yaml"),
        "supported_modes": ["image", "video"],
    }
