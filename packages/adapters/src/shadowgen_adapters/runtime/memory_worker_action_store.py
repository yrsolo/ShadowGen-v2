from __future__ import annotations

from copy import deepcopy

from shadowgen_contracts import WorkerActionRecord


class MemoryWorkerActionStore:
    def __init__(self) -> None:
        self._items: list[WorkerActionRecord] = []

    def enqueue(self, action: WorkerActionRecord) -> WorkerActionRecord:
        self._items.append(deepcopy(action))
        return action

    def take_next(self) -> WorkerActionRecord | None:
        pending = [item for item in self._items if item.status == "queued"]
        if not pending:
            return None
        pending.sort(key=lambda item: item.requested_at)
        action = pending[0]
        action.status = "running"
        self.update(action)
        return deepcopy(action)

    def update(self, action: WorkerActionRecord) -> WorkerActionRecord:
        for index, item in enumerate(self._items):
            if item.command_id == action.command_id:
                self._items[index] = deepcopy(action)
                break
        else:
            self._items.append(deepcopy(action))
        return action

    def list_recent(self, limit: int = 20) -> list[WorkerActionRecord]:
        items = sorted(self._items, key=lambda item: item.requested_at, reverse=True)
        return [deepcopy(item) for item in items[:limit]]
