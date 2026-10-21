"""
GET /results/{result_id}

All processing today is synchronous (see services/results_store.py), so
this always returns status="completed" -- but the response shape is
the future-friendly one from the spec (id, status, progress, output,
analytics), so switching to background processing later only changes
what create() gets called with and when, not this route or its schema.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.models.response import ResultResponse
from app.services.results_store import ResultsStore, get_results_store

router = APIRouter(tags=["results"])


@router.get("/results/{result_id}", response_model=ResultResponse)
def get_result(result_id: str, store: ResultsStore = Depends(get_results_store)) -> ResultResponse:
    record = store.get(result_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No result found with that id.")
    return ResultResponse(**record)
