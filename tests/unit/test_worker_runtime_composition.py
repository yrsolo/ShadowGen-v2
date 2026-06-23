import sys
from types import SimpleNamespace

from shadowgen_contracts import LocalRuntimeConfig
from shadowgen_worker.config import WorkerConfig

sys.modules.setdefault("docker", SimpleNamespace(from_env=lambda: None))
from shadowgen_worker import main as worker_main  # noqa: E402


def test_worker_runtime_reuses_ml_adapter_until_effective_url_changes(monkeypatch) -> None:
    created = []

    class FakeMLCorePipelineAdapter:
        def __init__(
            self,
            base_url: str | None = None,
            timeout_sec: float = 120.0,
            capabilities_refresh_interval_sec: float = 45.0,
        ) -> None:
            self.base_url = base_url
            self.timeout_sec = timeout_sec
            self.capabilities_refresh_interval_sec = capabilities_refresh_interval_sec
            created.append(self)

    monkeypatch.setattr(worker_main, "MLCorePipelineAdapter", FakeMLCorePipelineAdapter)
    config = WorkerConfig(
        state_backend="memory",
        queue_backend="memory",
        legacy_ml_base_url="http://ml-one:9001",
        worker_workspace_mount_dest=".",
    )

    runtime, _state_service, worker_loop, _control_loop, _control_app = worker_main.build_worker_runtime(config)

    first = worker_loop.executor.process_job_use_case_factory()
    second = worker_loop.executor.process_job_use_case_factory()

    assert first.pipeline is second.pipeline
    assert len(created) == 1
    assert created[0].base_url == "http://ml-one:9001"

    runtime.runtime_config_store.update(LocalRuntimeConfig(legacy_ml_base_url="http://ml-two:9001"))
    third = worker_loop.executor.process_job_use_case_factory()

    assert third.pipeline is not first.pipeline
    assert len(created) == 2
    assert created[1].base_url == "http://ml-two:9001"
