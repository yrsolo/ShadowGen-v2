from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class WorkerControlLoop:
    action_store: object
    executor: object
    poll_interval_sec: float = 1.0
    last_tick_at_monotonic: float | None = None
    last_error: str | None = None

    def tick(self) -> bool:
        action = self.action_store.take_next()
        if action is None:
            return False
        self.executor.execute(action)
        return True

    def run_forever(self) -> None:
        while True:
            self.last_tick_at_monotonic = time.monotonic()
            try:
                processed = self.tick()
            except Exception as exc:
                self.last_error = str(exc)
                time.sleep(self.poll_interval_sec)
                continue
            self.last_error = None
            self.last_tick_at_monotonic = time.monotonic()
            if not processed:
                time.sleep(self.poll_interval_sec)
