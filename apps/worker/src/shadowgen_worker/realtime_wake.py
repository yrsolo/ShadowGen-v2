from __future__ import annotations

import json
import time
from threading import Event

import httpx

from shadowgen_contracts import JobWakeCommand


class RealtimeWakeListener:
    def __init__(
        self,
        base_url: str,
        worker_id: str,
        worker_token: str,
        wake_event: Event,
        reconnect_min_sec: float = 1.0,
        reconnect_max_sec: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.worker_id = worker_id
        self.worker_token = worker_token
        self.wake_event = wake_event
        self.reconnect_min_sec = max(0.1, reconnect_min_sec)
        self.reconnect_max_sec = max(self.reconnect_min_sec, reconnect_max_sec)

    def run_forever(self) -> None:
        backoff = self.reconnect_min_sec
        while True:
            try:
                self._listen_once()
                backoff = self.reconnect_min_sec
            except Exception as exc:
                print(f"[ShadowGen Worker] realtime wake listener disconnected: {exc}", flush=True)
                time.sleep(backoff)
                backoff = min(self.reconnect_max_sec, backoff * 2)

    def _listen_once(self) -> None:
        url = f"{self.base_url}/internal/v1/workers/{self.worker_id}/wake"
        headers = {
            "Authorization": f"Bearer {self.worker_token}",
            "Accept": "text/event-stream",
        }
        with httpx.stream("GET", url, headers=headers, timeout=None) as response:
            response.raise_for_status()
            event_name: str | None = None
            data_lines: list[str] = []
            for line in response.iter_lines():
                if line == "":
                    self._handle_sse(event_name, data_lines)
                    event_name = None
                    data_lines = []
                    continue
                if line.startswith("event:"):
                    event_name = line.removeprefix("event:").strip()
                elif line.startswith("data:"):
                    data_lines.append(line.removeprefix("data:").strip())

    def _handle_sse(self, event_name: str | None, data_lines: list[str]) -> None:
        if event_name != "job_wake" or not data_lines:
            return
        payload = json.loads("\n".join(data_lines))
        JobWakeCommand.model_validate(payload)
        self.wake_event.set()
