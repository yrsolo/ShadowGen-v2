from __future__ import annotations

import json
from pathlib import Path

from shadowgen_contracts import JobRecord


class FileJobRepository:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def create(self, job: JobRecord) -> None:
        self._write(job)

    def get(self, job_id: str) -> JobRecord | None:
        path = self.root_dir / f"{job_id}.json"
        if not path.exists():
            return None
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, job: JobRecord) -> None:
        self._write(job)

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        records = [
            JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.root_dir.glob("*.json")
        ]
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def _write(self, job: JobRecord) -> None:
        path = self.root_dir / f"{job.job_id}.json"
        path.write_text(job.model_dump_json(indent=2), encoding="utf-8")
