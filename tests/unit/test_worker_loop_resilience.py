import time

from shadowgen_adapters.queue.memory_job_queue import InMemoryJobQueue
from shadowgen_adapters.runtime.memory_worker_state_store import MemoryWorkerStateStore
from shadowgen_contracts import RenderJobQueuedMessage
from shadowgen_worker.loop import WorkerLoop
from shadowgen_worker.state import WorkerStateService
from shadowgen_contracts import WorkerVersionInfo


class MemoryRuntimeConfigStore:
    def get(self):
        from shadowgen_contracts import LocalRuntimeConfig

        return LocalRuntimeConfig()


class ExplodingExecutor:
    def execute(self, job_id: str):
        raise RuntimeError(f"failed job {job_id}")


def test_worker_loop_does_not_crash_on_job_error() -> None:
    queue = InMemoryJobQueue()
    queue.publish(RenderJobQueuedMessage(job_id="job-1"))
    state_store = MemoryWorkerStateStore()
    state_service = WorkerStateService(
        worker_state_store=state_store,
        runtime_config_store=MemoryRuntimeConfigStore(),
        config_legacy_base_url="http://ml:9001",
        version_info=WorkerVersionInfo(),
    )
    loop = WorkerLoop(queue=queue, executor=ExplodingExecutor(), state_service=state_service, poll_interval_sec=0.01)

    processed = False
    for _ in range(20):
        processed = loop.tick() or processed
        if state_store.get().status == "error":
            break
        time.sleep(0.01)

    assert processed is True
    state = state_store.get()
    assert state.status == "error"
    assert state.last_job_id == "job-1"
    assert "failed job job-1" in (state.last_error or "")
    assert queue.consume().job_id == "job-1"
