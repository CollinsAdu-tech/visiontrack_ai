"""
Video processing pipelines:
  process_video()         -- per-frame detect -> annotate -> write (Phase 3, no identity)
  process_tracked_video() -- per-frame track  -> annotate -> write (Phase 4, persistent IDs)

Memory note: OpenCV's VideoCapture/VideoWriter work frame-by-frame, so
we never hold the whole decoded video in memory -- only ever one frame
at a time. The uploaded bytes are written to a temp file first because
cv2.VideoCapture needs a seekable file path, not an in-memory buffer;
that temp file is deleted after processing (see docs/privacy policy).
"""

import time
from contextlib import contextmanager
from pathlib import Path

import cv2

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.analytics import AnalyticsAccumulator, VideoAnalytics
from app.services.annotation import annotate_image, annotate_tracks, draw_count_event, draw_counting_line
from app.services.counter import LineCounter
from app.services.trajectory import TrajectoryStore
from app.utils.files import safe_output_filename

logger = get_logger(__name__)

# mp4v is broadly available in opencv-python without extra system codecs.
_FOURCC = "mp4v"


class VideoProcessingResult:
    def __init__(self, output_path: Path, analytics: VideoAnalytics):
        self.output_path = output_path
        self.analytics = analytics


@contextmanager
def _video_io(video_bytes: bytes, original_ext: str):
    """
    Shared setup/teardown for both video pipelines: write the upload to a
    temp file, open a VideoCapture + matching VideoWriter, and guarantee
    both the temp input and the OpenCV handles are cleaned up afterward.

    Yields (capture, writer, source_fps, width, height, output_path).
    """
    settings = get_settings()

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_input_path = upload_dir / safe_output_filename(original_ext)
    temp_input_path.write_bytes(video_bytes)

    capture = None
    writer = None
    try:
        capture = cv2.VideoCapture(str(temp_input_path))
        if not capture.isOpened():
            raise ValueError(
                "Could not open video -- the file may be corrupt or use an unsupported codec."
            )

        source_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / safe_output_filename(".mp4")

        fourcc = cv2.VideoWriter_fourcc(*_FOURCC)
        writer = cv2.VideoWriter(str(output_path), fourcc, source_fps, (width, height))
        if not writer.isOpened():
            raise ValueError("Could not create output video writer for this format.")

        yield capture, writer, source_fps, width, height, output_path
    finally:
        if capture is not None:
            capture.release()
        if writer is not None:
            writer.release()
        # Privacy: don't retain the uploaded source longer than needed to process it.
        temp_input_path.unlink(missing_ok=True)


def process_video(video_bytes: bytes, original_ext: str, detector) -> VideoProcessingResult:
    """
    Detection only, no identity across frames.
    `detector` is duck-typed on `.predict(frame) -> list[Detection]`.
    """
    with _video_io(video_bytes, original_ext) as (capture, writer, source_fps, _width, _height, output_path):
        accumulator = AnalyticsAccumulator()
        start_time = time.monotonic()

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            detections = detector.predict(frame)
            annotated = annotate_image(frame, detections)
            writer.write(annotated)

            accumulator.record_frame(class_names=[d.class_name for d in detections])

        elapsed = time.monotonic() - start_time
        analytics = accumulator.finalize(source_fps, elapsed)

    logger.info(
        "Processed video: %d frame(s) in %.2fs (%.2f fps) -> %s",
        analytics.frames_processed,
        analytics.processing_seconds,
        analytics.processing_fps,
        output_path,
    )
    return VideoProcessingResult(output_path=output_path, analytics=analytics)


def process_tracked_video(
    video_bytes: bytes,
    original_ext: str,
    tracker,
    counting_enabled: bool = True,
) -> VideoProcessingResult:
    """
    Detection + persistent tracking IDs + bounded trajectory history +
    (optionally) entry/exit counting across a virtual line.

    `tracker` is duck-typed on `.reset()` and `.track(frame) -> list[Track]`.

    Calls tracker.reset() first so IDs from a previous, unrelated video
    upload don't leak into this one (see Tracker.reset() docstring). A
    fresh TrajectoryStore and LineCounter are created per call for the
    same reason -- neither trajectories nor counts carry over between
    unrelated videos.

    The counting line is positioned as a ratio of this video's actual
    frame size (see core/config.py counting_line_*_ratio), so the same
    config works at any resolution.
    """
    tracker.reset()
    settings = get_settings()
    trajectory_store = TrajectoryStore(max_length=settings.trajectory_length)

    with _video_io(video_bytes, original_ext) as (capture, writer, source_fps, width, height, output_path):
        line_start = (
            settings.counting_line_start_ratio[0] * width,
            settings.counting_line_start_ratio[1] * height,
        )
        line_end = (
            settings.counting_line_end_ratio[0] * width,
            settings.counting_line_end_ratio[1] * height,
        )
        counter = LineCounter(line_start, line_end) if counting_enabled else None

        accumulator = AnalyticsAccumulator()
        start_time = time.monotonic()

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            tracks = tracker.track(frame)
            events: list[tuple[str, tuple[float, float]]] = []

            for track in tracks:
                center = (track.center_x, track.center_y)
                previous_center = trajectory_store.update(track.track_id, center, accumulator.frames_processed)

                if counter is not None:
                    event = counter.update(track.track_id, previous_center, center)
                    if event is not None:
                        events.append((event, center))

            trajectories = {t.track_id: trajectory_store.get_trajectory(t.track_id) for t in tracks}
            annotated = annotate_tracks(frame, tracks, trajectories=trajectories)
            if counter is not None:
                annotated = draw_counting_line(annotated, line_start, line_end)
            for event, position in events:
                annotated = draw_count_event(annotated, position, event)
            writer.write(annotated)

            accumulator.record_frame(
                class_names=[t.class_name for t in tracks],
                track_ids=[t.track_id for t in tracks],
            )

        elapsed = time.monotonic() - start_time
        analytics = accumulator.finalize(
            source_fps,
            elapsed,
            entries=counter.entries if counter is not None else 0,
            exits=counter.exits if counter is not None else 0,
        )

    logger.info(
        "Tracked video: %d frame(s), %d unique object(s), entries=%s exits=%s, %.2f fps -> %s",
        analytics.frames_processed,
        analytics.unique_tracked_objects,
        analytics.entries,
        analytics.exits,
        analytics.processing_fps,
        output_path,
    )
    return VideoProcessingResult(output_path=output_path, analytics=analytics)
