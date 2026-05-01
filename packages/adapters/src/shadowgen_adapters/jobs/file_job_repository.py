from __future__ import annotations

import json
from pathlib import Path

from shadowgen_contracts import JobRecord


class FileJobRepository:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.index_dir = self.root_dir / "_request-cache"
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def create(self, job: JobRecord) -> None:
        self._write(job)

    def get(self, job_id: str) -> JobRecord | None:
        path = self.root_dir / f"{job_id}.json"
        if not path.exists():
            return None
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, job: JobRecord) -> None:
        self._write(job)

    def find_by_request_cache_key(self, cache_key: str) -> JobRecord | None:
        indexed = self._get_indexed(cache_key)
        if indexed is not None:
            return indexed
        matches = []
        for path in self.root_dir.glob("*.json"):
            job = JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
            if job.request_cache_key == cache_key:
                matches.append(job)
        if not matches:
            return None
        matches.sort(key=lambda item: item.updated_at, reverse=True)
        return matches[0]

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
        if job.request_cache_key:
            (self.index_dir / f"{job.request_cache_key}.json").write_text(
                json.dumps({"job_id": job.job_id}, indent=2),
                encoding="utf-8",
            )

    def _get_indexed(self, cache_key: str) -> JobRecord | None:
        path = self.index_dir / f"{cache_key}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        job_id = payload.get("job_id")
        if not job_id:
            return None
        job = self.get(job_id)
        if job is None or job.request_cache_key != cache_key:
            return None
        return job
