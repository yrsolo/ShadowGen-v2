from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from shadowgen_contracts import JobRecord, JobRealtimeEvent, JobStatus, WorkerCapabilitySnapshot, WorkerInFlightJob


class RealtimePublishingObserver:
    def __init__(self, wrapped, realtime_accelerator, worker_id: str) -> None:
        self.wrapped = wrapped
        self.realtime_accelerator = realtime_accelerator
        self.worker_id = worker_id

    def capabilities_refreshed(self, snapshot: WorkerCapabilitySnapshot) -> None:
        self.wrapped.capabilities_refreshed(snapshot)

    def job_submitted(self, state: WorkerInFlightJob) -> None:
        self.wrapped.job_submitted(state)
        self._publish(
            JobRealtimeEvent(
                event_id=str(uuid4()),
                event_type="job_worker_seen",
                job_id=state.business_job_id,
                status=JobStatus.RUNNING,
                occurred_at=datetime.now(timezone.utc),
                source="worker",
                worker_id=self.worker_id,
                result_available=False,
            )
        )

    def job_polled(self, state: WorkerInFlightJob) -> None:
        self.wrapped.job_polled(state)

    def job_finished(self, job: JobRecord) -> None:
        self.wrapped.job_finished(job)
        self._publish(
            JobRealtimeEvent(
                event_id=str(uuid4()),
                event_type="job_succeeded",
                job_id=job.job_id,
                status=job.status,
                occurred_at=job.finished_at or datetime.now(timezone.utc),
                updated_at=job.updated_at,
                source="worker",
                worker_id=self.worker_id,
                result_available=True,
                duration_ms=_duration_ms(job.started_at, job.finished_at),
            )
        )

    def job_failed(self, job_id: str, error_text: str, failure_stage: str | None = None) -> None:
        self.wrapped.job_failed(job_id, error_text, failure_stage)
        self._publish(
            JobRealtimeEvent(
                event_id=str(uuid4()),
                event_type="job_failed",
                job_id=job_id,
                status=JobStatus.FAILED,
                occurred_at=datetime.now(timezone.utc),
                source="worker",
                worker_id=self.worker_id,
                result_available=True,
                error_code=failure_stage,
                error_message=error_text,
            )
        )

    def _publish(self, event: JobRealtimeEvent) -> None:
        try:
            self.realtime_accelerator.notify_job_event(event)
        except Exception:
            pass


def _duration_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return int((end - start).total_seconds() * 1000)
