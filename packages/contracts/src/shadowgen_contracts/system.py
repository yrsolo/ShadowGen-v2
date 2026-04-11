from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkerControlAction = Literal[
    "restart_worker_process",
    "restart_container",
    "git_update_rebuild_restart",
    "clear_runtime_override",
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
    version: WorkerVersionInfo = WorkerVersionInfo()
    last_action: WorkerActionRecord | None = None


__all__ = [
    "LocalRuntimeConfig",
    "UpdateLocalRuntimeConfigRequest",
    "UpdateLocalRuntimeConfigResponse",
    "WorkerActionRecord",
    "WorkerActionStatus",
    "WorkerControlAction",
    "WorkerJobSummary",
    "WorkerRuntimeState",
    "WorkerVersionInfo",
    "CreateWorkerActionRequest",
    "CreateWorkerActionResponse",
]
