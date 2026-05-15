from dataclasses import dataclass
from datetime import datetime

from .exceptions import JobStateError
from .statuses import JobStatus


@dataclass(slots=True)
class JobEntity:
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    def start(self, now: datetime) -> None:
        self._require_status(JobStatus.QUEUED, "start")
        self.status = JobStatus.RUNNING
        self.started_at = now
        self.updated_at = now

    def complete(self, now: datetime) -> None:
        self._require_status(JobStatus.RUNNING, "complete")
        self.status = JobStatus.SUCCEEDED
        self.finished_at = now
        self.updated_at = now

    def fail(self, now: datetime) -> None:
        if self.status.is_terminal:
            raise JobStateError(f"Cannot fail terminal job '{self.job_id}' from state '{self.status.value}'.")
        self.status = JobStatus.FAILED
        self.finished_at = now
        self.updated_at = now

    def cancel(self, now: datetime) -> None:
        if self.status.is_terminal:
            raise JobStateError(f"Cannot cancel terminal job '{self.job_id}' from state '{self.status.value}'.")
        self.status = JobStatus.CANCELED
        self.finished_at = now
        self.updated_at = now

    def _require_status(self, expected: JobStatus, action: str) -> None:
        if self.status != expected:
            raise JobStateError(
                f"Cannot {action} job '{self.job_id}' from state '{self.status.value}'; expected '{expected.value}'."
            )
