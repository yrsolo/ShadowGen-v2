import time
from threading import Event

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


class BlockingExecutor:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.calls: list[str] = []

    def execute(self, job_id: str):
        self.calls.append(job_id)
        self.started.set()
        self.release.wait(timeout=5)


class RecordingDelivery:
    def __init__(self, job_id: str) -> None:
        self.message = RenderJobQueuedMessage(job_id=job_id)
        self.acked = False
        self.nacked = False
        self.visibility_extensions: list[int] = []

    def ack(self) -> None:
        self.acked = True

    def nack(self) -> None:
        self.nacked = True

    def extend_visibility(self, timeout_sec: int) -> None:
        self.visibility_extensions.append(timeout_sec)


class ScriptedQueue:
    def __init__(self, deliveries: list[RecordingDelivery]) -> None:
        self.deliveries = deliveries

    def receive(self):
        if not self.deliveries:
            return None
        return self.deliveries.pop(0)


def make_state_service() -> WorkerStateService:
    return WorkerStateService(
        worker_state_store=MemoryWorkerStateStore(),
        runtime_config_store=MemoryRuntimeConfigStore(),
        config_legacy_base_url="http://ml:9001",
        version_info=WorkerVersionInfo(),
    )


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
        if state_store.get().last_error:
            break
        time.sleep(0.01)

    assert processed is True
    state = state_store.get()
    assert state.status == "idle"
    assert state.last_job_id == "job-1"
    assert "failed job job-1" in (state.last_error or "")
    assert queue.consume().job_id == "job-1"


def test_worker_loop_extends_visibility_for_long_running_job() -> None:
    delivery = RecordingDelivery("job-1")
    queue = ScriptedQueue([delivery])
    executor = BlockingExecutor()
    loop = WorkerLoop(
        queue=queue,
        executor=executor,
        state_service=make_state_service(),
        max_in_flight_jobs=1,
        queue_visibility_timeout_sec=45,
        queue_visibility_extend_interval_sec=1,
    )

    assert loop.tick() is True
    assert executor.started.wait(timeout=1)
    time.sleep(1.05)
    assert loop.tick() is True

    executor.release.set()
    for _ in range(20):
        loop.tick()
        if delivery.acked:
            break
        time.sleep(0.01)

    assert delivery.visibility_extensions == [45, 45]
    assert delivery.acked is True
    assert delivery.nacked is False


def test_worker_loop_does_not_start_duplicate_active_job_delivery() -> None:
    first = RecordingDelivery("job-1")
    duplicate = RecordingDelivery("job-1")
    queue = ScriptedQueue([first, duplicate])
    executor = BlockingExecutor()
    loop = WorkerLoop(
        queue=queue,
        executor=executor,
        state_service=make_state_service(),
        max_in_flight_jobs=2,
        queue_visibility_timeout_sec=60,
    )

    assert loop.tick() is True
    assert executor.started.wait(timeout=1)
    executor.release.set()
    for _ in range(20):
        loop.tick()
        if duplicate.acked:
            break
        time.sleep(0.01)

    assert executor.calls == ["job-1"]
    assert first.acked is False
    assert first.nacked is False
    assert duplicate.visibility_extensions == [60]
    assert duplicate.acked is True
    assert duplicate.nacked is False


def test_worker_loop_wake_interrupts_idle_sleep_without_direct_execution() -> None:
    wake_event = Event()
    queue = ScriptedQueue([])
    executor = BlockingExecutor()
    loop = WorkerLoop(
        queue=queue,
        executor=executor,
        state_service=make_state_service(),
        poll_interval_sec=10,
        wake_event=wake_event,
    )

    wake_event.set()
    started_at = time.monotonic()
    loop._sleep_until_poll_or_wake()

    assert time.monotonic() - started_at < 1
    assert executor.calls == []
