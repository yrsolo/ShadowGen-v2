from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class FileQueueDelivery:
    def __init__(self, pending_path: Path, claimed_path: Path, message: RenderJobQueuedMessage) -> None:
        self.pending_path = pending_path
        self.claimed_path = claimed_path
        self.message = message
        self._done = False

    def ack(self) -> None:
        if self._done:
            return
        self.claimed_path.unlink(missing_ok=True)
        self._done = True

    def nack(self) -> None:
        if self._done:
            return
        target = self.pending_path
        if target.exists():
            target = target.with_name(f"{self.message.job_id}-{uuid4()}.json")
        try:
            os.replace(self.claimed_path, target)
        except FileNotFoundError:
            pass
        self._done = True

    def extend_visibility(self, timeout_sec: int) -> None:
        _ = timeout_sec


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
        delivery = self.receive()
        if delivery is None:
            return None
        delivery.ack()
        return delivery.message

    def receive(self) -> FileQueueDelivery | None:
        for path in sorted(self.pending_dir.glob("*.json"), key=lambda item: item.name):
            claimed = path.with_suffix(".claimed")
            try:
                os.replace(path, claimed)
            except FileNotFoundError:
                continue
            data = claimed.read_text(encoding="utf-8")
            return FileQueueDelivery(path, claimed, RenderJobQueuedMessage.model_validate_json(data))
        return None

    def diagnostics(self) -> QueueDiagnostics:
        return QueueDiagnostics(
            backend="file",
            queued_count=len(list(self.pending_dir.glob("*.json"))),
            in_flight_count=len(list(self.pending_dir.glob("*.claimed"))),
            notes=[f"Queue path: {self.pending_dir}"],
        )
