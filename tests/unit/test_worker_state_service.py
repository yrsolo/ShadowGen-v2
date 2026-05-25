from datetime import datetime, timedelta, timezone

from shadowgen_contracts import (
    LocalRuntimeConfig,
    WorkerCapabilitySnapshot,
    WorkerDiagnosticProbe,
    WorkerInFlightJob,
    WorkerRuntimeState,
    WorkerVersionInfo,
)
from shadowgen_worker.state import WorkerStateService


class CountingWorkerStateStore:
    def __init__(self) -> None:
        self._state = WorkerRuntimeState()
        self.get_calls = 0
        self.update_calls = 0

    def get(self) -> WorkerRuntimeState:
        self.get_calls += 1
        return self._state.model_copy(deep=True)

    def update(self, state: WorkerRuntimeState) -> WorkerRuntimeState:
        self.update_calls += 1
        self._state = state.model_copy(deep=True)
        return self._state.model_copy(deep=True)


class CountingRuntimeConfigStore:
    def __init__(self) -> None:
        self._config = LocalRuntimeConfig()
        self.get_calls = 0

    def get(self) -> LocalRuntimeConfig:
        self.get_calls += 1
        return self._config.model_copy(deep=True)

    def update(self, config: LocalRuntimeConfig) -> LocalRuntimeConfig:
        self._config = config.model_copy(deep=True)
        return self._config.model_copy(deep=True)


def test_worker_state_service_avoids_idle_write_spam(monkeypatch) -> None:
    store = CountingWorkerStateStore()
    runtime_config_store = CountingRuntimeConfigStore()
    clock = {"now": datetime(2026, 4, 9, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr("shadowgen_worker.state.utc_now", lambda: clock["now"])
    service = WorkerStateService(
        worker_state_store=store,
        runtime_config_store=runtime_config_store,
        config_legacy_base_url="http://ml:9001",
        version_info=WorkerVersionInfo(git_commit="abc123"),
        idle_heartbeat_interval_sec=60.0,
    )

    service.boot()
    assert store.get_calls == 1
    assert store.update_calls == 1

    clock["now"] += timedelta(seconds=5)
    service.heartbeat_idle()
    assert store.get_calls == 1
    assert store.update_calls == 1

    runtime_config_store.update(LocalRuntimeConfig(legacy_ml_base_url="http://override:9001"))
    clock["now"] += timedelta(seconds=5)
    service.heartbeat_idle()
    assert store.update_calls == 2
    assert store.get().effective_legacy_base_url == "http://override:9001"

    clock["now"] += timedelta(seconds=10)
    service.heartbeat_idle()
    assert store.update_calls == 2

    clock["now"] += timedelta(seconds=61)
    service.heartbeat_idle()
    assert store.update_calls == 3


def test_worker_state_service_boot_is_idempotent_once_initialized(monkeypatch) -> None:
    store = CountingWorkerStateStore()
    runtime_config_store = CountingRuntimeConfigStore()
    clock = {"now": datetime(2026, 4, 9, 13, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr("shadowgen_worker.state.utc_now", lambda: clock["now"])
    service = WorkerStateService(
        worker_state_store=store,
        runtime_config_store=runtime_config_store,
        config_legacy_base_url=None,
        version_info=WorkerVersionInfo(),
        idle_heartbeat_interval_sec=60.0,
    )

    service.boot()
    clock["now"] += timedelta(seconds=1)
    service.boot()

    assert store.get_calls == 1
    assert store.update_calls == 1


def test_worker_state_service_tracks_capabilities_and_in_flight_jobs(monkeypatch) -> None:
    store = CountingWorkerStateStore()
    runtime_config_store = CountingRuntimeConfigStore()
    clock = {"now": datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr("shadowgen_worker.state.utc_now", lambda: clock["now"])
    service = WorkerStateService(
        worker_state_store=store,
        runtime_config_store=runtime_config_store,
        config_legacy_base_url="http://ml-core:9001",
        version_info=WorkerVersionInfo(git_commit="abc123"),
        idle_heartbeat_interval_sec=60.0,
    )

    service.boot()
    service.capabilities_refreshed(
        WorkerCapabilitySnapshot(
            async_enabled=True,
            execution_default_backend="triton",
            refreshed_at=clock["now"],
        )
    )
    service.job_submitted(
        WorkerInFlightJob(
            business_job_id="job-async-1",
            mode="async",
            status="queued",
            ml_core_job_id="ml-1",
            submit_started_at=clock["now"],
        )
    )

    state = store.get()
    assert state.ml_core_mode == "async"
    assert state.async_enabled is True
    assert state.status == "processing"
    assert len(state.in_flight_jobs) == 1
    assert state.in_flight_jobs[0].ml_core_job_id == "ml-1"

    clock["now"] += timedelta(seconds=2)
    service.job_polled(
        WorkerInFlightJob(
            business_job_id="job-async-1",
            mode="async",
            status="running",
            ml_core_job_id="ml-1",
            submit_started_at=state.in_flight_jobs[0].submit_started_at,
            last_poll_at=clock["now"],
        )
    )

    state = store.get()
    assert state.last_poll_error is None
    assert state.in_flight_jobs[0].status == "running"


def test_worker_state_service_clears_stale_capability_status_when_ml_url_changes(monkeypatch) -> None:
    store = CountingWorkerStateStore()
    runtime_config_store = CountingRuntimeConfigStore()
    clock = {"now": datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr("shadowgen_worker.state.utc_now", lambda: clock["now"])
    service = WorkerStateService(
        worker_state_store=store,
        runtime_config_store=runtime_config_store,
        config_legacy_base_url="http://old-ml:9001",
        version_info=WorkerVersionInfo(git_commit="abc123"),
        idle_heartbeat_interval_sec=60.0,
    )

    service.boot()
    service.capabilities_refreshed(
        WorkerCapabilitySnapshot(
            async_enabled=False,
            degraded=True,
            refreshed_at=clock["now"],
            notes=["Falling back to legacy sync path: Client error '404 NOT FOUND' for url 'http://old-ml:9001/health'"],
        )
    )

    runtime_config_store.update(LocalRuntimeConfig(legacy_ml_base_url="http://new-ml:9001"))
    clock["now"] += timedelta(seconds=1)
    service.heartbeat_idle()

    state = store.get()
    assert state.effective_legacy_base_url == "http://new-ml:9001"
    assert state.capabilities is None
    assert state.ml_core_mode is None
    assert state.async_enabled is None
    assert state.capability_refresh_error is None
    assert state.transition_fallback_active is False
    assert state.last_ml_probe is None


def test_worker_state_service_records_diagnostic_probe(monkeypatch) -> None:
    store = CountingWorkerStateStore()
    runtime_config_store = CountingRuntimeConfigStore()
    clock = {"now": datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr("shadowgen_worker.state.utc_now", lambda: clock["now"])
    service = WorkerStateService(
        worker_state_store=store,
        runtime_config_store=runtime_config_store,
        config_legacy_base_url="http://ml:9001",
        version_info=WorkerVersionInfo(git_commit="abc123"),
        idle_heartbeat_interval_sec=60.0,
    )

    service.boot()
    service.diagnostic_probe(
        WorkerDiagnosticProbe(checked_at=clock["now"], ok=True, latency_ms=1, mode="worker-control"),
        WorkerDiagnosticProbe(checked_at=clock["now"], ok=True, target_url="http://ml:9001", latency_ms=12, mode="legacy-sync"),
    )

    state = store.get()
    assert state.last_worker_probe is not None
    assert state.last_ml_probe is not None
    assert state.last_ml_probe.ok is True
    assert state.last_ml_probe.mode == "legacy-sync"
