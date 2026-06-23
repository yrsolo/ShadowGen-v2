from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from shadowgen_contracts import JobRealtimeEvent


@dataclass(slots=True)
class _JobEventState:
    events: list[JobRealtimeEvent] = field(default_factory=list)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)


class EventBuffer:
    def __init__(self, retention_sec: int = 300) -> None:
        self.retention = timedelta(seconds=max(1, retention_sec))
        self._jobs: dict[str, _JobEventState] = {}
        self._event_ids: set[str] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: JobRealtimeEvent) -> bool:
        async with self._lock:
            self._prune_locked()
            if event.event_id in self._event_ids:
                return False
            state = self._jobs.setdefault(event.job_id, _JobEventState())
            state.events.append(event)
            self._event_ids.add(event.event_id)
        async with state.condition:
            state.condition.notify_all()
        return True

    async def list_events(self, job_id: str, last_event_id: str | None = None) -> list[JobRealtimeEvent]:
        async with self._lock:
            self._prune_locked()
            state = self._jobs.get(job_id)
            if state is None:
                return []
            if not last_event_id:
                return list(state.events)
            for index, event in enumerate(state.events):
                if event.event_id == last_event_id:
                    return list(state.events[index + 1 :])
            return list(state.events)

    async def wait_for_event(self, job_id: str, timeout_sec: int) -> None:
        async with self._lock:
            state = self._jobs.setdefault(job_id, _JobEventState())
        async with state.condition:
            try:
                await asyncio.wait_for(state.condition.wait(), timeout=max(1, timeout_sec))
            except asyncio.TimeoutError:
                return

    async def job_count(self) -> int:
        async with self._lock:
            self._prune_locked()
            return len(self._jobs)

    def _prune_locked(self) -> None:
        cutoff = datetime.now(timezone.utc) - self.retention
        remaining_ids: set[str] = set()
        empty_job_ids: list[str] = []
        for job_id, state in self._jobs.items():
            state.events = [event for event in state.events if event.occurred_at >= cutoff]
            if not state.events:
                empty_job_ids.append(job_id)
                continue
            remaining_ids.update(event.event_id for event in state.events)
        for job_id in empty_job_ids:
            self._jobs.pop(job_id, None)
        self._event_ids = remaining_ids


def encode_sse(event: JobRealtimeEvent) -> str:
    payload = event.model_dump_json()
    return f"id: {event.event_id}\nevent: {event.event_type}\ndata: {payload}\n\n"


def encode_keepalive() -> str:
    return "event: keepalive\ndata: {}\n\n"
