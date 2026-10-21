"""
ResultsStore -- a minimal, in-memory registry mapping a result_id to a
completed processing result.

For this MVP, every /detect/image and /track/video call is still fully
synchronous -- the client gets the whole result in one response. But we
register every result here too, under a generated id, so:
  1. GET /results/{result_id} works today (re-fetch a result you already have)
  2. Swapping to background/async processing later only means changing
     *when* a result gets registered (immediately -> after a queued job
     finishes) -- not changing this interface or the route that reads it.

This is process-memory only (a plain dict): results are lost on
restart, and this does not scale across multiple worker processes. A
real deployment would replace this with a database or job queue -- see
docs/architecture.md limitations.
"""

import uuid
from functools import lru_cache


class ResultsStore:
    def __init__(self):
        self._results: dict[str, dict] = {}

    def create(self, media_type: str, output_url: str, analytics: dict | None = None, detections: list | None = None) -> str:
        result_id = uuid.uuid4().hex[:12]
        self._results[result_id] = {
            "id": result_id,
            "status": "completed",
            "progress": 100,
            "media_type": media_type,
            "output_url": output_url,
            "analytics": analytics,
            "detections": detections,
        }
        return result_id

    def get(self, result_id: str) -> dict | None:
        return self._results.get(result_id)


@lru_cache
def get_results_store() -> ResultsStore:
    """Process-wide singleton. See module docstring for its limitations."""
    return ResultsStore()
