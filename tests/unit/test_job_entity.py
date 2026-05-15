from datetime import datetime, timezone

import pytest

from shadowgen_domain import JobEntity, JobStateError, JobStatus


def test_job_entity_happy_path_lifecycle() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    started_at = datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    finished_at = datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
    job = JobEntity(
        job_id="job-1",
        status=JobStatus.QUEUED,
        created_at=created_at,
        updated_at=created_at,
    )

    job.start(started_at)
    job.complete(finished_at)

    assert job.status == JobStatus.SUCCEEDED
    assert job.started_at == started_at
    assert job.finished_at == finished_at
    assert job.is_terminal is True


def test_job_entity_rejects_invalid_transition() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    job = JobEntity(
        job_id="job-1",
        status=JobStatus.SUCCEEDED,
        created_at=now,
        updated_at=now,
        finished_at=now,
    )

    with pytest.raises(JobStateError):
        job.start(now)
