"""
Full-stack test of section 39's second flow:
    Upload video -> API -> video processor -> detector/tracker -> counter -> output

Uses the real FastAPI routing/multipart parsing/response validation,
with only the ML calls stubbed out via dependency_overrides.
"""


def test_detect_video_end_to_end(client, stub_detector, make_mp4_bytes):
    response = client.post(
        "/detect/video",
        files={"file": ("sample.mp4", make_mp4_bytes(frame_count=4), "video/mp4")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["media_type"] == "video"
    assert body["analytics"]["frames_processed"] == 4
    assert body["analytics"]["object_counts"] == {"person": 4}
    assert body["output_url"].startswith("/outputs/")
    assert "result_id" in body


def test_track_video_end_to_end(client, stub_tracker, make_mp4_bytes):
    response = client.post(
        "/track/video",
        files={"file": ("sample.mp4", make_mp4_bytes(frame_count=4), "video/mp4")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    analytics = body["analytics"]
    assert analytics["frames_processed"] == 4
    assert analytics["unique_tracked_objects"] == 1  # same track_id=1 every frame
    assert analytics["current_objects"] == 1
    assert "result_id" in body


def test_track_video_resets_tracker_state_per_request(client, stub_tracker, make_mp4_bytes):
    video_bytes = make_mp4_bytes(frame_count=3)

    client.post("/track/video", files={"file": ("a.mp4", video_bytes, "video/mp4")})
    client.post("/track/video", files={"file": ("b.mp4", video_bytes, "video/mp4")})

    assert stub_tracker.reset_calls == 2


def test_track_video_honors_counting_enabled_false(client, stub_tracker, make_mp4_bytes):
    response = client.post(
        "/track/video",
        data={"counting_enabled": "false"},
        files={"file": ("sample.mp4", make_mp4_bytes(frame_count=4), "video/mp4")},
    )

    assert response.status_code == 200
    analytics = response.json()["analytics"]
    assert analytics["entries"] == 0
    assert analytics["exits"] == 0


def test_detect_video_rejects_corrupt_file(client, stub_detector):
    response = client.post(
        "/detect/video",
        files={"file": ("broken.mp4", b"not a real video file", "video/mp4")},
    )
    assert response.status_code == 422


def test_track_video_rejects_unsupported_extension(client, stub_tracker, make_mp4_bytes):
    response = client.post(
        "/track/video",
        files={"file": ("sample.gif", make_mp4_bytes(frame_count=2), "image/gif")},
    )
    assert response.status_code == 415
