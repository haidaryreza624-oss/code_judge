from fastapi import APIRouter, HTTPException

from app.schemas.submission import SubmissionRequest
from app.services.queue_manager import queue_manager

router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["Submissions"]
)


@router.post("/", status_code=202)
async def create_submission(data: SubmissionRequest):

    job = await queue_manager.submit(data)

    if job is None:
        raise HTTPException(
            status_code=503,
            detail="Queue is full. Try again later."
        )

    return job


@router.get("/{job_id}")
async def get_submission(job_id: str):

    job = await queue_manager.get_job(job_id)

    if job is None:
        raise HTTPException(404, "Job not found")

    return job