from datetime import datetime, timezone

from shadowgen_contracts import ErrorInfo, JobRecord, JobStatus, JobTraceStage
from shadowgen_domain import JobNotFoundError

from shadowgen_application.ports import JobRepositoryPort


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ManageJobUseCase:
    def __init__(self, job_repository: JobRepositoryPort) -> None:
        self.job_repository = job_repository

    def mark_failed(self, job_id: str, reason: str) -> JobRecord:
        job = self._get_job(job_id)
        now = utc_now()
        job.status = JobStatus.FAILED
        job.updated_at = now
        job.finished_at = job.finished_at or now
        job.error = ErrorInfo(code="operator_marked_failed", message=reason)
        job.trace.append(
            JobTraceStage(
                name="operator_mark_failed",
                status="failed",
                started_at=now,
                finished_at=now,
                duration_ms=0,
                message="Operator marked the job failed from diagnostics.",
                error=reason,
            )
        )
        self.job_repository.update(job)
        return job

    def delete(self, job_id: str) -> None:
        job = self._get_job(job_id)
        self.job_repository.delete(job)

    def _get_job(self, job_id: str) -> JobRecord:
        job = self.job_repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job '{job_id}' was not found.")
        return job
