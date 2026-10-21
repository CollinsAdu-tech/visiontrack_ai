"""
Detection -- a single application-level bounding box result.

Deliberately decoupled from Ultralytics' Results/Boxes objects so the
rest of the app (routes, annotation, tracking in a later phase) depends
on this stable shape instead of a third-party library's internals. If
we ever swap detection frameworks, only detector.py needs to change.
"""

from pydantic import BaseModel, computed_field


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @computed_field
    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @computed_field
    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @computed_field
    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @computed_field
    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2
