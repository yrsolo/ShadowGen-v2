from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class FileJobQueue:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.pending_dir = self.root_dir / "pending"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, message: RenderJobQueuedMessage) -> None:
        filename = f"{message.job_id}-{uuid4()}.json"
        path = self.pending_dir / filename
        path.write_text(message.model_dump_json(indent=2), encoding="utf-8")

    def consume(self) -> RenderJobQueuedMessage | None:
        for path in sorted(self.pending_dir.glob("*.json"), key=lambda item: item.name):
            claimed = path.with_suffix(".claimed")
            try:
                os.replace(path, claimed)
            except FileNotFoundError:
                continue
            data = claimed.read_text(encoding="utf-8")
            claimed.unlink(missing_ok=True)
            return RenderJobQueuedMessage.model_validate_json(data)
        return None

    def diagnostics(self) -> QueueDiagnostics:
        return QueueDiagnostics(
            backend="file",
            queued_count=len(list(self.pending_dir.glob("*.json"))),
            in_flight_count=0,
            notes=[f"Queue path: {self.pending_dir}"],
        )
