from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from .errors import ErrorInfo
from .render import RenderRequest, RenderResult
from .enums import JobStatus
from .realtime import RealtimeSubscription


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateJobRequest(BaseModel):
    render: RenderRequest


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


class JobTimingMetrics(BaseModel):
    queue_wait_ms: int | None = None
    pre_start_worker_ms: int | None = None
    worker_duration_ms: int | None = None
    ml_total_ms: int | None = None
    worker_overhead_ms: int | None = None
    ml_poll_overhead_ms: int | None = None


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    cache_status: str | None = None
    reused_existing_job: bool = False
    job: JobRecord | None = None
    timing: JobTimingMetrics | None = None
    realtime: RealtimeSubscription | None = None


class GetJobResponse(BaseModel):
    job: JobRecord
    timing: JobTimingMetrics | None = None
    realtime: RealtimeSubscription | None = None


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


class ClearJobCacheResponse(BaseModel):
    cleared_entries: int


def derive_job_timing_metrics(job: JobRecord) -> JobTimingMetrics:
    worker_claimed = _first_stage(job, "worker_claimed")
    ml_poll = _first_stage(job, "ml_poll")
    worker_duration_ms = _duration_ms(job.started_at, job.finished_at)
    ml_total_ms = job.result.metrics.total_ms if job.result is not None else None
    return JobTimingMetrics(
        queue_wait_ms=_duration_ms(job.created_at, worker_claimed.started_at if worker_claimed is not None else None),
        pre_start_worker_ms=_duration_ms(worker_claimed.started_at if worker_claimed is not None else None, job.started_at),
        worker_duration_ms=worker_duration_ms,
        ml_total_ms=ml_total_ms,
        worker_overhead_ms=_subtract(worker_duration_ms, ml_total_ms),
        ml_poll_overhead_ms=_subtract(ml_poll.duration_ms if ml_poll is not None else None, ml_total_ms),
    )


def _first_stage(job: JobRecord, name: str) -> JobTraceStage | None:
    for stage in job.trace:
        if stage.name == name:
            return stage
    return None


def _duration_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return int((end - start).total_seconds() * 1000)


def _subtract(left: int | None, right: int | None) -> int | None:
    if left is None or right is None:
        return None
    return left - right


__all__ = [
    "ClearJobCacheResponse",
    "CreateJobRequest",
    "CreateJobResponse",
    "GetJobResponse",
    "GetJobResultResponse",
    "JobTimingMetrics",
    "JobMutationResponse",
    "JobRecord",
    "JobTraceStage",
    "MarkJobFailedRequest",
    "RenderJobQueuedMessage",
    "derive_job_timing_metrics",
]
