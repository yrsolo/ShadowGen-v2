from datetime import datetime

from pydantic import BaseModel

from .jobs import JobRecord
from .system import LocalRuntimeConfig, WorkerActionRecord, WorkerJobSummary, WorkerRuntimeState


class QueueDiagnostics(BaseModel):
    backend: str
    queued_count: int | None = None
    in_flight_count: int | None = None
    notes: list[str] = []


class WorkerDiagnostics(BaseModel):
    render_backend: str
    legacy_base_url: str | None = None
    live_legacy_available: bool | None = None
    runtime_state: WorkerRuntimeState | None = None
    ml_core_mode: str | None = None
    async_enabled: bool | None = None
    heartbeat_age_sec: int | None = None
    heartbeat_is_stale: bool | None = None
    effective_legacy_base_url: str | None = None
    capabilities_refreshed_at: datetime | None = None
    capability_refresh_error: str | None = None
    in_flight_count: int = 0
    recent_completed_jobs: list[WorkerJobSummary] = []
    failed_jobs_count: int = 0
    recent_failures: list[JobRecord] = []
    recent_actions: list[WorkerActionRecord] = []


class StorageDiagnostics(BaseModel):
    backend: str
    bucket: str | None = None
    prefix: str | None = None
    notes: list[str] = []


class LostJobDiagnostic(BaseModel):
    job: JobRecord
    age_sec: int
    reason: str
    evidence: list[str] = []
    suggested_action: str = "mark_failed"


class SystemDiagnosticsResponse(BaseModel):
    app_env: str
    storage: StorageDiagnostics
    queue: QueueDiagnostics
    worker: WorkerDiagnostics
    runtime_config: LocalRuntimeConfig
    recent_jobs: list[JobRecord]
    lost_jobs: list[LostJobDiagnostic] = []


__all__ = ["LostJobDiagnostic", "QueueDiagnostics", "StorageDiagnostics", "SystemDiagnosticsResponse", "WorkerDiagnostics"]
