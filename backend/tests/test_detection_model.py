from app.models.detection import Detection


def test_detection_geometry_properties():
    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.91,
        x1=100.0,
        y1=50.0,
        x2=200.0,
        y2=250.0,
    )
    assert det.width == 100.0
    assert det.height == 200.0
    assert det.center_x == 150.0
    assert det.center_y == 150.0
