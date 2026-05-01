from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock

from shadowgen_application.ports import RuntimeConfigStorePort, WorkerStateStorePort
from shadowgen_contracts import (
    JobRecord,
    WorkerActionRecord,
    WorkerCapabilitySnapshot,
    WorkerInFlightJob,
    WorkerRuntimeState,
    WorkerVersionInfo,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class WorkerStateService:
    worker_state_store: WorkerStateStorePort
    runtime_config_store: RuntimeConfigStorePort
    config_legacy_base_url: str | None
    version_info: WorkerVersionInfo
    idle_heartbeat_interval_sec: float = 30.0
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)
    _state: WorkerRuntimeState | None = field(default=None, init=False, repr=False)

    def boot(self) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            now = utc_now()
            changed = False
            if state.startup_at is None:
                state.startup_at = now
                changed = True
            if state.status != "idle" and not state.in_flight_jobs:
                state.status = "idle"
                changed = True
            changed = self._sync_runtime_metadata_locked(state) or changed
            if state.updated_at is None:
                changed = True
            if not changed:
                return state.model_copy(deep=True)
            state.updated_at = now
            return self._persist_locked()

    def effective_legacy_base_url(self) -> str | None:
        runtime_config = self.runtime_config_store.get()
        return runtime_config.legacy_ml_base_url or self.config_legacy_base_url

    def heartbeat_idle(self) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            now = utc_now()
            changed = False
            if not state.in_flight_jobs and state.status != "idle" and state.last_error is None:
                state.status = "idle"
                changed = True
            changed = self._sync_runtime_metadata_locked(state) or changed
            if not changed and not self._heartbeat_due_locked(now, state):
                return state.model_copy(deep=True)
            state.updated_at = now
            return self._persist_locked()

    def capabilities_refreshed(self, snapshot: WorkerCapabilitySnapshot) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            state.capabilities = snapshot.model_copy(deep=True)
            state.ml_core_mode = "async" if snapshot.async_enabled else "sync"
            state.async_enabled = snapshot.async_enabled
            state.transition_fallback_active = snapshot.degraded
            state.capability_refresh_error = "; ".join(snapshot.notes) if snapshot.degraded and snapshot.notes else None
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def job_submitted(self, in_flight_job: WorkerInFlightJob) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            self._upsert_in_flight_locked(state, in_flight_job)
            state.status = "processing"
            state.last_job_id = in_flight_job.business_job_id
            state.current_job_id = state.in_flight_jobs[0].business_job_id if state.in_flight_jobs else in_flight_job.business_job_id
            state.current_job_started_at = state.in_flight_jobs[0].submit_started_at if state.in_flight_jobs else in_flight_job.submit_started_at
            state.last_submit_error = None
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def job_polled(self, in_flight_job: WorkerInFlightJob) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            self._upsert_in_flight_locked(state, in_flight_job)
            state.status = "processing" if state.in_flight_jobs else "idle"
            state.last_job_id = in_flight_job.business_job_id
            state.current_job_id = state.in_flight_jobs[0].business_job_id if state.in_flight_jobs else None
            state.current_job_started_at = state.in_flight_jobs[0].submit_started_at if state.in_flight_jobs else None
            state.last_poll_error = in_flight_job.last_error
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def job_finished(self, job: JobRecord) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            state.in_flight_jobs = [item for item in state.in_flight_jobs if item.business_job_id != job.job_id]
            state.status = "processing" if state.in_flight_jobs else "idle"
            state.last_job_id = job.job_id
            state.current_job_id = state.in_flight_jobs[0].business_job_id if state.in_flight_jobs else None
            state.current_job_started_at = state.in_flight_jobs[0].submit_started_at if state.in_flight_jobs else None
            state.last_error = None
            state.last_submit_error = None
            state.last_poll_error = None
            state.last_completed_job_id = job.job_id
            if job.started_at is not None and job.finished_at is not None:
                state.last_completed_duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def job_failed(self, job_id: str, error_text: str) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            state.in_flight_jobs = [item for item in state.in_flight_jobs if item.business_job_id != job_id]
            state.status = "error" if not state.in_flight_jobs else "processing"
            state.last_job_id = job_id
            state.current_job_id = state.in_flight_jobs[0].business_job_id if state.in_flight_jobs else None
            state.current_job_started_at = state.in_flight_jobs[0].submit_started_at if state.in_flight_jobs else None
            state.last_error = error_text
            state.last_submit_error = error_text
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def action_state(self, action: WorkerActionRecord) -> WorkerRuntimeState:
        with self._lock:
            state = self._ensure_state_loaded_locked()
            state.last_action = action
            state.updated_at = utc_now()
            self._sync_runtime_metadata_locked(state)
            return self._persist_locked()

    def _ensure_state_loaded_locked(self) -> WorkerRuntimeState:
        if self._state is None:
            self._state = self.worker_state_store.get().model_copy(deep=True)
        return self._state

    def _sync_runtime_metadata_locked(self, state: WorkerRuntimeState) -> bool:
        changed = False
        effective_base_url = self.effective_legacy_base_url()
        if state.effective_legacy_base_url != effective_base_url:
            state.effective_legacy_base_url = effective_base_url
            changed = True
        if state.version.model_dump(mode="json") != self.version_info.model_dump(mode="json"):
            state.version = self.version_info.model_copy(deep=True)
            changed = True
        return changed

    def _heartbeat_due_locked(self, now: datetime, state: WorkerRuntimeState) -> bool:
        if state.updated_at is None:
            return True
        return (now - state.updated_at).total_seconds() >= self.idle_heartbeat_interval_sec

    def _upsert_in_flight_locked(self, state: WorkerRuntimeState, in_flight_job: WorkerInFlightJob) -> None:
        replacement = in_flight_job.model_copy(deep=True)
        for index, item in enumerate(state.in_flight_jobs):
            if item.business_job_id == replacement.business_job_id:
                state.in_flight_jobs[index] = replacement
                break
        else:
            state.in_flight_jobs.append(replacement)

    def _persist_locked(self) -> WorkerRuntimeState:
        payload = self._ensure_state_loaded_locked().model_copy(deep=True)
        persisted = self.worker_state_store.update(payload)
        self._state = persisted.model_copy(deep=True)
        return self._state.model_copy(deep=True)
