from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import Job, JobStatus


class SubmitJobRequest(BaseModel):
    id: UUID
    project_id: UUID | None = Field(None, description="Project ID")
    model_revision_id: UUID | None = Field(None, description="Model revision ID")
    payload: dict | None  = Field(None, description="Training job configuration")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "project_id": "7b073838-99d3-42ff-9018-4e901eb047fc",
                "model_revision_id": "a22d82ba-afa9-4d6e-bbc1-8c8e4002ec29",
                "payload": {
                    "epochs": 10,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                },
            }
        }
    }

class JobView(BaseModel):
    id: UUID
    status: JobStatus
    progress: float
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "completed",
            }
        }
    }

    @staticmethod
    def of(job: Job) -> "JobView":
        return JobView(
            id=job.id,
            status=job.status,
            progress=job.progress,
            started_at=datetime.fromtimestamp(job.started_at, tz=timezone.utc) if job.started_at else None,
            finished_at=datetime.fromtimestamp(job.updated_at, tz=timezone.utc) if job.status in (JobStatus.DONE, JobStatus.FAILED) else None
        )
