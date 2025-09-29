import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status, Depends, Request, HTTPException
from starlette.responses import StreamingResponse

from app.job_queue import JobsQueue
from app.models import Job, JobStatus, now_utc_ts
from app.routers.depedencies import get_queue
from app.schema import JobView, SubmitJobRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("", response_model=JobView, status_code=status.HTTP_202_ACCEPTED)
async def submit(req: SubmitJobRequest, queue: Annotated[JobsQueue, Depends(get_queue)]) -> JobView:
    job = Job(id = req.id, status=JobStatus.PENDING, submitted_at=now_utc_ts())
    await queue.submit(job)
    return JobView.of(job)

@router.get("", response_model=list[JobView])
async def list_jobs(queue: Annotated[JobsQueue, Depends(get_queue)]) -> list[JobView]:
    return [JobView.of(job) for job in queue.list_all()]

@router.get("/{job_id}", response_model=JobView)
async def get_job(job_id: UUID, queue: Annotated[JobsQueue, Depends(get_queue)]) -> JobView:
    job = queue.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobView.of(job)

@router.get("/{job_id}/stream")
async def stream(job_id: UUID, request: Request, queue: Annotated[JobsQueue, Depends(get_queue)]):
    if not queue.get(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def gen():
        last = None
        while True:
            if await request.is_disconnected():
                break
            j = queue.get(job_id)
            if not j:
                break
            snap = json.dumps(JobView.of(j).model_dump_json())
            logger.info(f"Snap: {snap}")
            if snap != last:
                yield f"data: {snap}\n\n"
                last = snap
            if j.status in (JobStatus.DONE, JobStatus.FAILED):
                break
            await asyncio.sleep(0.1)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    })
