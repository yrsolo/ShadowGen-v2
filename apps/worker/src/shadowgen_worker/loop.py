from __future__ import annotations

import time
from dataclasses import dataclass
from concurrent.futures import Future, ThreadPoolExecutor


@dataclass(slots=True)
class _InFlightDelivery:
    delivery: object
    last_visibility_extend_at: float


class WorkerLoop:
    def __init__(
        self,
        queue,
        executor,
        state_service,
        poll_interval_sec: float = 1.0,
        max_in_flight_jobs: int = 4,
        queue_visibility_timeout_sec: int = 120,
        queue_visibility_extend_interval_sec: int = 30,
    ) -> None:
        self.queue = queue
        self.executor = executor
        self.state_service = state_service
        self.poll_interval_sec = poll_interval_sec
        self.max_in_flight_jobs = max(1, max_in_flight_jobs)
        self.queue_visibility_timeout_sec = max(1, queue_visibility_timeout_sec)
        self.queue_visibility_extend_interval_sec = max(1, queue_visibility_extend_interval_sec)
        self._pool = ThreadPoolExecutor(max_workers=self.max_in_flight_jobs, thread_name_prefix="shadowgen-worker")
        self._in_flight: dict[Future, _InFlightDelivery] = {}
        self._job_futures: dict[str, Future] = {}

    def tick(self) -> bool:
        processed = self._drain_finished()
        self._extend_in_flight_visibility()
        while len(self._in_flight) < self.max_in_flight_jobs:
            delivery = self.queue.receive()
            if delivery is None:
                break
            existing_future = self._job_futures.get(delivery.message.job_id)
            if existing_future is not None:
                self._replace_active_delivery(existing_future, delivery)
                processed = True
                continue
            self._extend_delivery_visibility(delivery)
            future = self._pool.submit(self.executor.execute, delivery.message.job_id)
            self._in_flight[future] = _InFlightDelivery(
                delivery=delivery,
                last_visibility_extend_at=time.monotonic(),
            )
            self._job_futures[delivery.message.job_id] = future
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
            in_flight = self._in_flight.pop(future)
            delivery = in_flight.delivery
            job_id = delivery.message.job_id
            self._job_futures.pop(job_id, None)
            try:
                future.result()
            except Exception as exc:
                self.state_service.job_failed(job_id, str(exc))
                delivery.nack()
            else:
                delivery.ack()
            processed = True
        return processed

    def _extend_in_flight_visibility(self) -> None:
        now = time.monotonic()
        for in_flight in self._in_flight.values():
            if now - in_flight.last_visibility_extend_at < self.queue_visibility_extend_interval_sec:
                continue
            self._extend_delivery_visibility(in_flight.delivery)
            in_flight.last_visibility_extend_at = now

    def _replace_active_delivery(self, future: Future, delivery) -> None:
        self._extend_delivery_visibility(delivery)
        self._in_flight[future] = _InFlightDelivery(
            delivery=delivery,
            last_visibility_extend_at=time.monotonic(),
        )

    def _extend_delivery_visibility(self, delivery) -> None:
        try:
            delivery.extend_visibility(self.queue_visibility_timeout_sec)
        except Exception:
            pass
