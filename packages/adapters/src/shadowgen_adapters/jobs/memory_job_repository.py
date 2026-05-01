from shadowgen_contracts import JobRecord


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._storage: dict[str, JobRecord] = {}
        self._request_cache_index: dict[str, str] = {}

    def create(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job
        self._index(job)

    def get(self, job_id: str) -> JobRecord | None:
        return self._storage.get(job_id)

    def update(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job
        self._index(job)

    def find_by_request_cache_key(self, cache_key: str) -> JobRecord | None:
        indexed_job_id = self._request_cache_index.get(cache_key)
        if indexed_job_id is not None:
            indexed = self._storage.get(indexed_job_id)
            if indexed is not None and indexed.request_cache_key == cache_key:
                return indexed
        records = [
            item
            for item in self._storage.values()
            if item.request_cache_key == cache_key
        ]
        if not records:
            return None
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records[0]

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        records = sorted(self._storage.values(), key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def clear(self) -> None:
        self._storage.clear()
        self._request_cache_index.clear()

    def _index(self, job: JobRecord) -> None:
        if not job.request_cache_key:
            return
        self._request_cache_index[job.request_cache_key] = job.job_id
