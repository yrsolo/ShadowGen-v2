from __future__ import annotations

import json

from botocore.client import BaseClient

from shadowgen_adapters.object_storage import dump_json_bytes, prefixed_key
from shadowgen_contracts import WorkerActionRecord


class S3WorkerActionStore:
    def __init__(self, client: BaseClient, bucket: str, prefix: str) -> None:
        self.client = client
        self.bucket = bucket
        self.prefix = prefix

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

    @property
    def _key(self) -> str:
        return prefixed_key(self.prefix, "runtime/worker-actions.json")

    def _read(self) -> list[WorkerActionRecord]:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key)
        except self.client.exceptions.NoSuchKey:
            return []
        payload = json.loads(response["Body"].read().decode("utf-8"))
        return [WorkerActionRecord.model_validate(item) for item in payload]

    def _write(self, items: list[WorkerActionRecord]) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key,
            Body=dump_json_bytes([item.model_dump(mode="json") for item in items]),
            ContentType="application/json",
        )
