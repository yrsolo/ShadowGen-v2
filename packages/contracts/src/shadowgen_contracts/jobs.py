from datetime import datetime, timezone
from typing import Literal

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
    cache_status: str | None = None
    reused_existing_job: bool = False


class JobTraceStage(BaseModel):
    name: str
    status: Literal["running", "succeeded", "failed", "skipped"]
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    duration_ms: int | None = None
    message: str | None = None
    error: str | None = None


class RenderJobQueuedMessage(BaseModel):
    message_version: str = "1"
    job_id: str
    routing_key: str = "render.job.queued"


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    request: RenderRequest
    request_cache_key: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: ErrorInfo | None = None
    result: RenderResult | None = None
    trace: list[JobTraceStage] = Field(default_factory=list)
    cache_status: str | None = None
    reused_existing_job: bool = False


class GetJobResponse(BaseModel):
    job: JobRecord


class GetJobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: RenderResult | None = None


class MarkJobFailedRequest(BaseModel):
    reason: str = "Marked failed by operator."


class JobMutationResponse(BaseModel):
    job_id: str
    status: JobStatus | None = None
    deleted: bool = False


__all__ = [
    "CreateJobRequest",
    "CreateJobResponse",
    "GetJobResponse",
    "GetJobResultResponse",
    "JobMutationResponse",
    "JobRecord",
    "JobTraceStage",
    "MarkJobFailedRequest",
    "RenderJobQueuedMessage",
]
