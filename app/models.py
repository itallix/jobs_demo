from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"

def now_utc_ts() -> float:
    return datetime.now(tz=timezone.utc).timestamp()

class Job(BaseModel):
    id: UUID
    status: JobStatus
    submitted_at: float
    started_at: float | None = None
    updated_at: float = now_utc_ts()
    progress: float = 0.0  # percentage of completion
    result: dict | None = None  # result of the job, if completed
    error: str | None = None

    def start(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = now_utc_ts()
        self.updated_at = now_utc_ts()

    def advance(self, percent: float) -> None:
        self.progress = max(0.0, min(100.0, percent))
        self.updated_at = now_utc_ts()

    def finish(self) -> None:
        self.status = JobStatus.DONE
        self.progress = 100.0
        self.updated_at = now_utc_ts()

    def fail(self, msg: str) -> None:
        self.status = JobStatus.FAILED
        self.updated_at = now_utc_ts()
        self.error = msg
