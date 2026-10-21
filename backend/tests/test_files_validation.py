import io

import pytest
from fastapi import UploadFile

from app.utils.files import FileTooLarge, UnsupportedFileType, validate_image_upload


def _upload(filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(b"fake-bytes"))


def test_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileType):
        validate_image_upload(_upload("virus.exe"), b"data")


def test_accepts_supported_extension_under_size_limit():
    # Should not raise.
    validate_image_upload(_upload("photo.jpg"), b"small-image-bytes")


def test_rejects_file_over_size_limit(monkeypatch):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
    config.get_settings.cache_clear()

    oversized = b"x" * 2048
    with pytest.raises(FileTooLarge):
        validate_image_upload(_upload("photo.jpg"), oversized)

    config.get_settings.cache_clear()
