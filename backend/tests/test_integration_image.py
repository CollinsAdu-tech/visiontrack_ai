"""
Full-stack test of section 39's first flow:
    Upload image -> API -> model (stubbed) -> detections -> response

Uses the real FastAPI routing/multipart parsing/response validation,
with only the ML call itself stubbed out via dependency_overrides.
"""


def test_detect_image_end_to_end(client, stub_detector, tiny_jpg_bytes):
    response = client.post(
        "/detect/image",
        files={"file": ("sample.jpg", tiny_jpg_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["media_type"] == "image"
    assert len(body["detections"]) == 1
    assert body["detections"][0]["class_name"] == "person"
    assert body["object_counts"] == {"person": 1}
    assert body["output_url"].startswith("/outputs/")
    assert "result_id" in body


def test_detect_image_result_is_fetchable_afterward(client, stub_detector, tiny_jpg_bytes):
    post_response = client.post(
        "/detect/image",
        files={"file": ("sample.jpg", tiny_jpg_bytes, "image/jpeg")},
    )
    result_id = post_response.json()["result_id"]

    get_response = client.get(f"/results/{result_id}")
    assert get_response.status_code == 200
    record = get_response.json()
    assert record["status"] == "completed"
    assert record["media_type"] == "image"
    assert record["output_url"] == post_response.json()["output_url"]


def test_detect_image_rejects_unsupported_file_type(client, stub_detector):
    response = client.post(
        "/detect/image",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415


def test_detect_image_rejects_oversized_file(client, stub_detector, monkeypatch, tiny_jpg_bytes):
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
    config.get_settings.cache_clear()

    response = client.post(
        "/detect/image",
        files={"file": ("sample.jpg", tiny_jpg_bytes, "image/jpeg")},
    )
    assert response.status_code == 413

    config.get_settings.cache_clear()


def test_detect_image_requires_a_file(client):
    response = client.post("/detect/image")
    assert response.status_code == 422  # FastAPI's own request-shape validation
