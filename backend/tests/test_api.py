"""
Phase 1 tests: prove the app boots and the two foundation routes work.
Detection/tracking tests are added in later phases.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "VisionTrack AI"


def test_config_exposes_only_safe_fields():
    response = client.get("/config")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"model", "tracker", "supported_modes"}
    assert body["supported_modes"] == ["image", "video"]


def test_unknown_result_id_returns_404():
    response = client.get("/results/does-not-exist")
    assert response.status_code == 404
