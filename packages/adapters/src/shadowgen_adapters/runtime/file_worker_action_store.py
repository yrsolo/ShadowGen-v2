from __future__ import annotations

import json
from pathlib import Path

from shadowgen_contracts import WorkerActionRecord


class FileWorkerActionStore:
    def __init__(self, state_dir: str | Path) -> None:
        self.path = Path(state_dir) / "system" / "worker-actions.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def enqueue(self, action: WorkerActionRecord) -> WorkerActionRecord:
        items = self._read()
        items.append(action)
        self._write(items)
        return action

    def take_next(self) -> WorkerActionRecord | None:
        items = self._read()
        pending = [item for item in items if item.status == "queued"]
        if not pending:
            return None
        pending.sort(key=lambda item: item.requested_at)
        action = pending[0]
        action.status = "running"
        self.update(action)
        return action

    def update(self, action: WorkerActionRecord) -> WorkerActionRecord:
        items = self._read()
        for index, item in enumerate(items):
            if item.command_id == action.command_id:
                items[index] = action
                break
        else:
            items.append(action)
        self._write(items)
        return action

    def list_recent(self, limit: int = 20) -> list[WorkerActionRecord]:
        items = sorted(self._read(), key=lambda item: item.requested_at, reverse=True)
        return items[:limit]

    def _read(self) -> list[WorkerActionRecord]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [WorkerActionRecord.model_validate(item) for item in payload]

    def _write(self, items: list[WorkerActionRecord]) -> None:
        self.path.write_text(
            json.dumps([item.model_dump(mode="json") for item in items], ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
