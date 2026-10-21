from app.models.tracking import Track


def test_track_has_detection_geometry_plus_id():
    track = Track(
        track_id=17,
        class_id=0,
        class_name="person",
        confidence=0.88,
        x1=100.0,
        y1=50.0,
        x2=200.0,
        y2=250.0,
    )
    assert track.track_id == 17
    # Inherited from Detection -- should work without redefinition.
    assert track.width == 100.0
    assert track.center_x == 150.0
