from dataclasses import dataclass
from datetime import datetime, timezone

from shadowgen_application.ports import (
    JobRepositoryPort,
    QueueInspectorPort,
    RuntimeConfigStorePort,
    WorkerActionStorePort,
    WorkerStateStorePort,
)
from shadowgen_contracts import JobStatus, StorageDiagnostics, SystemDiagnosticsResponse, WorkerDiagnostics, WorkerJobSummary

WORKER_STALE_THRESHOLD_SEC = 300


@dataclass(slots=True)
class WorkerRuntimeInfo:
    render_backend: str
    legacy_base_url: str | None
    live_legacy_available: bool | None


@dataclass(slots=True)
class StorageRuntimeInfo:
    backend: str
    bucket: str | None
    prefix: str | None
    notes: list[str]


class GetSystemDiagnosticsUseCase:
    def __init__(
        self,
        app_env: str,
        job_repository: JobRepositoryPort,
        queue_inspector: QueueInspectorPort,
        runtime_config_store: RuntimeConfigStorePort,
        worker_state_store: WorkerStateStorePort,
        worker_action_store: WorkerActionStorePort,
        worker_runtime: WorkerRuntimeInfo,
        storage_runtime: StorageRuntimeInfo,
    ) -> None:
        self.app_env = app_env
        self.job_repository = job_repository
        self.queue_inspector = queue_inspector
        self.runtime_config_store = runtime_config_store
        self.worker_state_store = worker_state_store
        self.worker_action_store = worker_action_store
        self.worker_runtime = worker_runtime
        self.storage_runtime = storage_runtime

    def execute(self, limit: int = 10) -> SystemDiagnosticsResponse:
        recent_jobs = self.job_repository.list_recent(limit=max(limit, 30))
        recent_failures = [job for job in recent_jobs if job.status == JobStatus.FAILED][:5]
        recent_completed = [
            WorkerJobSummary(
                job_id=job.job_id,
                status=job.status.value,
                started_at=job.started_at,
                finished_at=job.finished_at,
                duration_ms=int((job.finished_at - job.started_at).total_seconds() * 1000)
                if job.started_at is not None and job.finished_at is not None
                else None,
                error_message=job.error.message if job.error else None,
            )
            for job in recent_jobs
            if job.status == JobStatus.SUCCEEDED
        ][:5]
        recent_actions = self.worker_action_store.list_recent(limit=5)
        runtime_state = self.worker_state_store.get()
        heartbeat_age_sec = None
        heartbeat_is_stale = None
        if runtime_state.updated_at is not None:
            heartbeat_age_sec = int((datetime.now(timezone.utc) - runtime_state.updated_at).total_seconds())
            heartbeat_is_stale = heartbeat_age_sec > WORKER_STALE_THRESHOLD_SEC
        return SystemDiagnosticsResponse(
            app_env=self.app_env,
            storage=StorageDiagnostics(
                backend=self.storage_runtime.backend,
                bucket=self.storage_runtime.bucket,
                prefix=self.storage_runtime.prefix,
                notes=self.storage_runtime.notes,
            ),
            queue=self.queue_inspector.diagnostics(),
            worker=WorkerDiagnostics(
                render_backend=self.worker_runtime.render_backend,
                legacy_base_url=self.worker_runtime.legacy_base_url,
                live_legacy_available=self.worker_runtime.live_legacy_available,
                runtime_state=runtime_state,
                ml_core_mode=runtime_state.ml_core_mode,
                async_enabled=runtime_state.async_enabled,
                heartbeat_age_sec=heartbeat_age_sec,
                heartbeat_is_stale=heartbeat_is_stale,
                effective_legacy_base_url=runtime_state.effective_legacy_base_url or self.worker_runtime.legacy_base_url,
                capabilities_refreshed_at=runtime_state.capabilities.refreshed_at if runtime_state.capabilities else None,
                capability_refresh_error=runtime_state.capability_refresh_error,
                in_flight_count=len(runtime_state.in_flight_jobs),
                recent_completed_jobs=recent_completed,
                failed_jobs_count=len([job for job in recent_jobs if job.status == JobStatus.FAILED]),
                recent_failures=recent_failures,
                recent_actions=recent_actions,
            ),
            runtime_config=self.runtime_config_store.get(),
            recent_jobs=recent_jobs[:limit],
        )
