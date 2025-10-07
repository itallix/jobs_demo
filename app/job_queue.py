import asyncio
import logging

from uuid import UUID

from app.models import Job, JobStatus

logger = logging.getLogger(__name__)


class JobsQueue:
    """Holds all jobs in memory: provides FIFO order and state queries."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self._by_id: dict[UUID, Job] = {}
        self._order: list[UUID] = [] # preserve submit order for listing
        self._lock = asyncio.Lock()

    async def submit(self, job: Job) -> None:
        """Submit a new job to the queue."""
        async with self._lock:
            self._by_id[job.id] = job
            self._order.append(job.id)
            logger.info("Submitted job", extra={"job_id": job.id})
            await self._queue.put(job)

    async def next_runnable(self) -> Job | None:
        """Get the next non-canceled job from the queue (FIFO order)."""
        while True:
            job = await self._queue.get()
            if job.status == JobStatus.CANCELLED:
                logger.info("Skipping cancelled job", extra={"job_id": job.id})
                continue
            logger.debug(
                "Retrieved job from queue",
                extra={"job_id": job.id, "status": job.status}
            )
            return job

    def get(self, job_id: UUID) -> Job | None:
        """Get a job by its ID."""
        return self._by_id.get(job_id)

    def list_all(self) -> list[Job]:
        """List all jobs."""
        return [self._by_id[jid] for jid in self._order if jid in self._by_id]

    def list_non_completed(self) -> list[Job]:
        """List all non-completed jobs."""
        return [job for job in self._by_id.values() if job.status < JobStatus.DONE]

    def cancel(self, job_id: UUID) -> bool:
        """Mark a job as cancelled. If the job is pending, it will be removed from the queue."""
        job = self._by_id.get(job_id)
        if not job or job.status >= JobStatus.DONE:
            return False
        if job.status == JobStatus.PENDING:
            job.cancel()
            logger.info("Cancelled pending job", extra={"job_id": job_id})
            return True
        elif job.status == JobStatus.RUNNING:
            job.cancelling()
            logger.info("Marked running job for cancellation", extra={"job_id": job_id})
            return True
        return False

    def is_cancelling(self, job_id: UUID) -> bool:
        """Check if a job is marked as being cancelled."""
        job = self._by_id.get(job_id)
        return job is not None and job.status == JobStatus.CANCELLING
