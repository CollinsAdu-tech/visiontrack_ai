"""
Draws detections/tracks onto an image -- the annotated result is what
the user actually sees in the response.

COLOR ORDER BUG (fixed): OpenCV expects colors as (B, G, R), not the
usual (R, G, B). Every constant below was originally written using RGB
hex values (from Flat UI Colors) without flipping the byte order, so
what was meant to be blue rendered as orange, red rendered as
blue/purple, and so on -- red and blue are near-complementary, which
is exactly why the mismatch was so obvious once someone actually
looked at real output. Caught on a real run, not by any automated test
(none of them visually inspect color). Every tuple below is now the
correct (B, G, R) for its named color.
"""

import cv2
import numpy as np

from app.models.detection import Detection
from app.models.tracking import Track

_BOX_COLOR = (113, 204, 46)   # emerald green (#2ecc71)
_TEXT_COLOR = (255, 255, 255)

# A small fixed palette so each track ID gets a stable, distinguishable
# color across frames (indexed by track_id % len(palette)).
_TRACK_PALETTE = [
    (113, 204, 46),   # green   (#2ecc71)
    (34, 126, 230),   # orange  (#e67e22)
    (219, 152, 52),   # blue    (#3498db)
    (60, 76, 231),    # red     (#e74c3c)
    (182, 89, 155),   # purple  (#9b59b6)
    (15, 196, 241),   # yellow  (#f1c40f)
]


def _draw_labeled_box(image: np.ndarray, x1: float, y1: float, x2: float, y2: float, label: str, color: tuple) -> None:
    p1 = (int(x1), int(y1))
    p2 = (int(x2), int(y2))
    cv2.rectangle(image, p1, p2, color, 2)

    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    label_bg_p2 = (p1[0] + text_w + 6, max(0, p1[1] - text_h - 8))
    cv2.rectangle(image, p1, label_bg_p2, color, -1)
    cv2.putText(
        image,
        label,
        (p1[0] + 3, max(12, p1[1] - 5)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        _TEXT_COLOR,
        1,
        cv2.LINE_AA,
    )


_LINE_COLOR = (219, 152, 52)      # blue (#3498db) -- counting line
_ENTRY_COLOR = (113, 204, 46)     # green (#2ecc71)
_EXIT_COLOR = (60, 76, 231)       # red (#e74c3c)


def draw_counting_line(image: np.ndarray, line_start: tuple[float, float], line_end: tuple[float, float]) -> np.ndarray:
    annotated = image.copy()
    p1 = (int(line_start[0]), int(line_start[1]))
    p2 = (int(line_end[0]), int(line_end[1]))
    cv2.line(annotated, p1, p2, _LINE_COLOR, 2, cv2.LINE_AA)
    cv2.putText(
        annotated, "COUNTING LINE", (p1[0] + 5, p1[1] - 8),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, _LINE_COLOR, 1, cv2.LINE_AA,
    )
    return annotated


def draw_count_event(image: np.ndarray, position: tuple[float, float], event: str) -> np.ndarray:
    """Flashes ENTRY/EXIT text on the frame where a crossing was just counted."""
    annotated = image.copy()
    color = _ENTRY_COLOR if event == "entry" else _EXIT_COLOR
    origin = (int(position[0]), int(position[1]))
    cv2.putText(annotated, event.upper(), origin, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    return annotated


def annotate_image(image: np.ndarray, detections: list[Detection]) -> np.ndarray:
    annotated = image.copy()
    for det in detections:
        label = f"{det.class_name} {det.confidence:.2f}"
        _draw_labeled_box(annotated, det.x1, det.y1, det.x2, det.y2, label, _BOX_COLOR)
    return annotated


def annotate_tracks(
    image: np.ndarray,
    tracks: list[Track],
    trajectories: dict[int, list[tuple[float, float]]] | None = None,
) -> np.ndarray:
    """
    Same as annotate_image, but labels include the persistent track ID.

    `trajectories`, if given, maps track_id -> recent center-point
    history (oldest to newest); each track's recent path is drawn as a
    thin polyline in that track's color before its box is drawn on top.
    """
    annotated = image.copy()

    if trajectories:
        for track in tracks:
            points = trajectories.get(track.track_id)
            if not points or len(points) < 2:
                continue
            color = _TRACK_PALETTE[track.track_id % len(_TRACK_PALETTE)]
            pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [pts], isClosed=False, color=color, thickness=2)

    for track in tracks:
        color = _TRACK_PALETTE[track.track_id % len(_TRACK_PALETTE)]
        label = f"{track.class_name} {track.confidence:.2f} | ID:{track.track_id}"
        _draw_labeled_box(annotated, track.x1, track.y1, track.x2, track.y2, label, color)

    return annotated
