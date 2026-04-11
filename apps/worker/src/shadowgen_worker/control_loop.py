from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class WorkerControlLoop:
    action_store: object
    executor: object
    poll_interval_sec: float = 1.0

    def tick(self) -> bool:
        action = self.action_store.take_next()
        if action is None:
            return False
        self.executor.execute(action)
        return True

    def run_forever(self) -> None:
        while True:
            if not self.tick():
                time.sleep(self.poll_interval_sec)
