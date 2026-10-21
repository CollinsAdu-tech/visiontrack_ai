"""
File validation and safe-filename utilities.

Never trust the client-supplied filename or Content-Type header alone --
validate extension against an allow-list, enforce a size cap, and
generate a fresh filename for anything we write to disk.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings


class UnsupportedFileType(Exception):
    pass


class FileTooLarge(Exception):
    pass


def _validate_upload(file: UploadFile, data: bytes, allowed_extensions: tuple[str, ...], kind: str) -> None:
    settings = get_settings()

    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise UnsupportedFileType(
            f"'{ext or 'unknown'}' is not a supported {kind} type. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise FileTooLarge(f"File exceeds the {settings.max_upload_size_mb}MB limit.")


def validate_image_upload(file: UploadFile, data: bytes) -> None:
    settings = get_settings()
    _validate_upload(file, data, settings.allowed_image_extensions, kind="image")


def validate_video_upload(file: UploadFile, data: bytes) -> None:
    settings = get_settings()
    _validate_upload(file, data, settings.allowed_video_extensions, kind="video")


def safe_output_filename(original_ext: str) -> str:
    """Generate a collision-safe filename; never reuse the client's own name."""
    return f"{uuid.uuid4().hex}{original_ext}"
