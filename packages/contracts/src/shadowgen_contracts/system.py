from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkerControlAction = Literal[
    "restart_worker_process",
    "restart_container",
    "git_update_rebuild_restart",
    "clear_runtime_override",
    "diagnostic_probe",
]

WorkerActionStatus = Literal["queued", "running", "succeeded", "failed"]


class LocalRuntimeConfig(BaseModel):
    legacy_ml_base_url: str | None = None


class UpdateLocalRuntimeConfigRequest(BaseModel):
    legacy_ml_base_url: str | None = None


class UpdateLocalRuntimeConfigResponse(BaseModel):
    config: LocalRuntimeConfig


class WorkerVersionInfo(BaseModel):
    git_branch: str | None = None
    git_commit: str | None = None
    image_tag: str | None = None
    container_name: str | None = None


class WorkerCapabilityComponent(BaseModel):
    name: str
    available: bool = True
    backend_kind: str | None = None
    model_variant: str | None = None
    supports_batching: bool = False
    supports_async: bool = False
    fallback_reason: str | None = None


class WorkerCapabilitySnapshot(BaseModel):
    async_enabled: bool | None = None
    execution_default_backend: str | None = None
    refreshed_at: datetime | None = None
    degraded: bool = False
    notes: list[str] = Field(default_factory=list)
    components: list[WorkerCapabilityComponent] = Field(default_factory=list)


class WorkerInFlightJob(BaseModel):
    business_job_id: str
    mode: str
    status: str = "submitting"
    ml_core_job_id: str | None = None
    request_id: str | None = None
    submit_started_at: datetime | None = None
    last_poll_at: datetime | None = None
    ttl_deadline_at: datetime | None = None
    retry_count: int = 0
    last_error: str | None = None


class WorkerJobSummary(BaseModel):
    job_id: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None


class WorkerActionRecord(BaseModel):
    command_id: str
    action: WorkerControlAction
    requested_at: datetime
    requested_by: str
    validation_marker: str | None = None
    payload: dict[str, str] = Field(default_factory=dict)
    status: WorkerActionStatus = "queued"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary: str | None = None
    error_text: str | None = None
    log_excerpt: str | None = None


class WorkerDiagnosticProbe(BaseModel):
    checked_at: datetime
    ok: bool
    target_url: str | None = None
    latency_ms: int | None = None
    mode: str | None = None
    error: str | None = None


class CreateWorkerActionRequest(BaseModel):
    action: WorkerControlAction


class CreateWorkerActionResponse(BaseModel):
    command: WorkerActionRecord


class WorkerRuntimeState(BaseModel):
    status: str = "idle"
    last_job_id: str | None = None
    last_error: str | None = None
    updated_at: datetime | None = None
    startup_at: datetime | None = None
    current_job_id: str | None = None
    current_job_started_at: datetime | None = None
    last_completed_job_id: str | None = None
    last_completed_duration_ms: int | None = None
    effective_legacy_base_url: str | None = None
    ml_core_mode: str | None = None
    async_enabled: bool | None = None
    capability_refresh_error: str | None = None
    capabilities: WorkerCapabilitySnapshot | None = None
    in_flight_jobs: list[WorkerInFlightJob] = Field(default_factory=list)
    last_submit_error: str | None = None
    last_poll_error: str | None = None
    transition_fallback_active: bool = False
    version: WorkerVersionInfo = WorkerVersionInfo()
    last_action: WorkerActionRecord | None = None
    last_worker_probe: WorkerDiagnosticProbe | None = None
    last_ml_probe: WorkerDiagnosticProbe | None = None


__all__ = [
    "LocalRuntimeConfig",
    "UpdateLocalRuntimeConfigRequest",
    "UpdateLocalRuntimeConfigResponse",
    "WorkerActionRecord",
    "WorkerActionStatus",
    "WorkerCapabilityComponent",
    "WorkerCapabilitySnapshot",
    "WorkerControlAction",
    "WorkerDiagnosticProbe",
    "WorkerInFlightJob",
    "WorkerJobSummary",
    "WorkerRuntimeState",
    "WorkerVersionInfo",
    "CreateWorkerActionRequest",
    "CreateWorkerActionResponse",
]
