from datetime import datetime, timedelta, timezone

from shadowgen_contracts import LocalRuntimeConfig, WorkerRuntimeState, WorkerVersionInfo
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
