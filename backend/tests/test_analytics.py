from app.services.analytics import AnalyticsAccumulator


def test_current_objects_reflects_only_the_most_recent_frame():
    acc = AnalyticsAccumulator()
    acc.record_frame(["person", "person"], track_ids=[1, 2])
    acc.record_frame(["person"], track_ids=[1])  # object 2 left the frame
    analytics = acc.finalize(source_fps=30.0, elapsed_seconds=1.0)

    assert analytics.current_objects == 1
    assert analytics.frames_processed == 2


def test_unique_tracked_objects_counts_distinct_ids_not_frame_appearances():
    acc = AnalyticsAccumulator()
    # Same 2 IDs seen across 5 frames -- should total 2 unique, not 10.
    for _ in range(5):
        acc.record_frame(["person", "person"], track_ids=[7, 8])
    analytics = acc.finalize(source_fps=30.0, elapsed_seconds=1.0)

    assert analytics.unique_tracked_objects == 2
    assert analytics.object_counts == {"person": 10}


def test_object_counts_aggregate_across_all_frames_by_class():
    acc = AnalyticsAccumulator()
    acc.record_frame(["person", "car"])
    acc.record_frame(["person"])
    analytics = acc.finalize(source_fps=30.0, elapsed_seconds=1.0)

    assert analytics.object_counts == {"person": 2, "car": 1}


def test_finalize_computes_duration_and_processing_fps():
    acc = AnalyticsAccumulator()
    for _ in range(60):
        acc.record_frame(["person"])
    analytics = acc.finalize(source_fps=30.0, elapsed_seconds=2.0)

    assert analytics.duration_seconds == 2.0   # 60 frames / 30 source fps
    assert analytics.processing_fps == 30.0    # 60 frames / 2.0s elapsed


def test_finalize_handles_zero_elapsed_and_zero_fps_without_crashing():
    acc = AnalyticsAccumulator()
    analytics = acc.finalize(source_fps=0.0, elapsed_seconds=0.0)

    assert analytics.duration_seconds == 0.0
    assert analytics.processing_fps == 0.0


def test_entries_and_exits_pass_through_to_the_final_summary():
    acc = AnalyticsAccumulator()
    acc.record_frame(["person"], track_ids=[1])
    analytics = acc.finalize(source_fps=30.0, elapsed_seconds=1.0, entries=3, exits=1)

    assert analytics.entries == 3
    assert analytics.exits == 1
