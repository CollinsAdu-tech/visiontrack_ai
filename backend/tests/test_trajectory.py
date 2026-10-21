from app.services.trajectory import TrajectoryStore


def test_update_returns_previous_center_and_none_on_first_sighting():
    store = TrajectoryStore(max_length=30)

    first = store.update(track_id=1, center=(10.0, 10.0), frame_index=0)
    assert first is None  # no previous point yet

    second = store.update(track_id=1, center=(12.0, 11.0), frame_index=1)
    assert second == (10.0, 10.0)

    assert store.get_trajectory(1) == [(10.0, 10.0), (12.0, 11.0)]


def test_history_is_bounded_to_max_length():
    store = TrajectoryStore(max_length=3)

    for i in range(10):
        store.update(track_id=1, center=(float(i), float(i)), frame_index=i)

    trajectory = store.get_trajectory(1)
    assert len(trajectory) == 3
    # Should hold only the most recent 3 points, oldest first.
    assert trajectory == [(7.0, 7.0), (8.0, 8.0), (9.0, 9.0)]


def test_separate_track_ids_have_independent_histories():
    store = TrajectoryStore(max_length=30)

    store.update(track_id=1, center=(0.0, 0.0), frame_index=0)
    store.update(track_id=2, center=(100.0, 100.0), frame_index=0)
    store.update(track_id=1, center=(1.0, 1.0), frame_index=1)

    assert store.get_trajectory(1) == [(0.0, 0.0), (1.0, 1.0)]
    assert store.get_trajectory(2) == [(100.0, 100.0)]


def test_first_and_last_seen_frame_tracked_per_id():
    store = TrajectoryStore(max_length=30)

    store.update(track_id=5, center=(0.0, 0.0), frame_index=10)
    store.update(track_id=5, center=(1.0, 1.0), frame_index=11)
    store.update(track_id=5, center=(2.0, 2.0), frame_index=12)

    assert store.first_seen_frame(5) == 10
    assert store.last_seen_frame(5) == 12
    assert store.first_seen_frame(999) is None


def test_unknown_track_returns_empty_trajectory():
    store = TrajectoryStore(max_length=30)
    assert store.get_trajectory(42) == []
