"""
Track -- a Detection that has been assigned a persistent identity by
the tracker across frames.

Deliberately a subclass of Detection rather than a separate shape: a
Track *is* a Detection plus one more fact (which object this is). Keeping
the inheritance keeps annotate_tracks() and any future analytics code
able to reuse Detection's geometry helpers for free.

Track vs Detection, concretely:
    Detection: "there is a person here, 0.91 confidence" (per-frame, no memory)
    Track:     "this is Person #17, 0.91 confidence"     (persists across frames)
"""

from app.models.detection import Detection


class Track(Detection):
    track_id: int
