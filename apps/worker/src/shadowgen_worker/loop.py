from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor


class WorkerLoop:
    def __init__(
        self,
        queue,
        executor,
        state_service,
        poll_interval_sec: float = 1.0,
        max_in_flight_jobs: int = 4,
    ) -> None:
        self.queue = queue
        self.executor = executor
        self.state_service = state_service
        self.poll_interval_sec = poll_interval_sec
        self.max_in_flight_jobs = max(1, max_in_flight_jobs)
        self._pool = ThreadPoolExecutor(max_workers=self.max_in_flight_jobs, thread_name_prefix="shadowgen-worker")
        self._in_flight: dict[Future, object] = {}

    def tick(self) -> bool:
        processed = self._drain_finished()
        while len(self._in_flight) < self.max_in_flight_jobs:
            delivery = self.queue.receive()
            if delivery is None:
                break
            future = self._pool.submit(self.executor.execute, delivery.message.job_id)
            self._in_flight[future] = delivery
            processed = True
        processed = self._drain_finished() or processed
        if not processed and not self._in_flight:
            self.state_service.heartbeat_idle()
            return False
        return processed or bool(self._in_flight)

    def run_forever(self):
        self.state_service.boot()
        while True:
            if not self.tick():
                time.sleep(self.poll_interval_sec)

    def _drain_finished(self) -> bool:
        processed = False
        completed = [future for future in self._in_flight if future.done()]
        for future in completed:
            delivery = self._in_flight.pop(future)
            job_id = delivery.message.job_id
            try:
                future.result()
            except Exception as exc:
                self.state_service.job_failed(job_id, str(exc))
                delivery.nack()
            else:
                delivery.ack()
            processed = True
        return processed
