from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .enums import JobStatus


RealtimeTransport = Literal["sse"]

JobRealtimeEventType = Literal[
    "connected",
    "job_queued",
    "job_running",
    "job_worker_seen",
    "job_succeeded",
    "job_failed",
    "job_canceled",
    "keepalive",
    "fallback_required",
]

JobRealtimeEventSource = Literal["api", "worker", "vps"]

WorkerRealtimeMessageType = Literal[
    "worker_hello",
    "worker_heartbeat",
    "worker_job_event",
    "job_wake",
]


class RealtimeSubscription(BaseModel):
    transport: RealtimeTransport = "sse"
    base_url: str
    path: str
    token: str
    expires_at: datetime
    fallback_poll_ms: int = 350


class JobRealtimeEvent(BaseModel):
    event_version: Literal["1"] = "1"
    event_id: str
    event_type: JobRealtimeEventType
    job_id: str
    status: JobStatus | None = None
    occurred_at: datetime
    updated_at: datetime | None = None
    source: JobRealtimeEventSource
    sequence: int | None = None
    cache_status: str | None = None
    reused_existing_job: bool | None = None
    worker_id: str | None = None
    result_available: bool = False
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None


class JobQueuedSignal(BaseModel):
    message_version: Literal["1"] = "1"
    event_id: str
    job_id: str
    status: Literal["queued"] = "queued"
    cache_status: str | None = None
    reused_existing_job: bool = False
    queued_at: datetime
    idempotency_key: str


class RealtimeAcceptedResponse(BaseModel):
    accepted: bool
    duplicate: bool = False


class WorkerHelloMessage(BaseModel):
    message_version: Literal["1"] = "1"
    message_type: Literal["worker_hello"] = "worker_hello"
    worker_id: str
    started_at: datetime
    max_in_flight_jobs: int
    async_enabled: bool | None = None
    mode: str | None = None


class WorkerHeartbeatMessage(BaseModel):
    message_version: Literal["1"] = "1"
    message_type: Literal["worker_heartbeat"] = "worker_heartbeat"
    worker_id: str
    sent_at: datetime
    in_flight_job_ids: list[str] = Field(default_factory=list)


class WorkerJobEventMessage(BaseModel):
    message_version: Literal["1"] = "1"
    message_type: Literal["worker_job_event"] = "worker_job_event"
    event_id: str
    worker_id: str
    job_id: str
    event_type: JobRealtimeEventType
    status: JobStatus | None = None
    occurred_at: datetime
    result_available: bool = False
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class JobWakeCommand(BaseModel):
    message_version: Literal["1"] = "1"
    message_type: Literal["job_wake"] = "job_wake"
    command_id: str
    job_id: str
    queued_at: datetime


__all__ = [
    "JobQueuedSignal",
    "JobRealtimeEvent",
    "JobRealtimeEventSource",
    "JobRealtimeEventType",
    "JobWakeCommand",
    "RealtimeAcceptedResponse",
    "RealtimeSubscription",
    "RealtimeTransport",
    "WorkerHeartbeatMessage",
    "WorkerHelloMessage",
    "WorkerJobEventMessage",
    "WorkerRealtimeMessageType",
]
