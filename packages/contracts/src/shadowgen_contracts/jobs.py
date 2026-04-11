from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .errors import ErrorInfo
from .render import RenderRequest, RenderResult
from .enums import JobStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateJobRequest(BaseModel):
    render: RenderRequest


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class RenderJobQueuedMessage(BaseModel):
    message_version: str = "1"
    job_id: str
    routing_key: str = "render.job.queued"


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    request: RenderRequest
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: ErrorInfo | None = None
    result: RenderResult | None = None


class GetJobResponse(BaseModel):
    job: JobRecord


class GetJobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: RenderResult | None = None


__all__ = [
    "CreateJobRequest",
    "CreateJobResponse",
    "GetJobResponse",
    "GetJobResultResponse",
    "JobRecord",
    "RenderJobQueuedMessage",
]
