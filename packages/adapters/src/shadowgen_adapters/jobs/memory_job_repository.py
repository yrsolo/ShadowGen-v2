from shadowgen_contracts import JobRecord


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._storage: dict[str, JobRecord] = {}

    def create(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job

    def get(self, job_id: str) -> JobRecord | None:
        return self._storage.get(job_id)

    def update(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        records = sorted(self._storage.values(), key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def clear(self) -> None:
        self._storage.clear()
