from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from shadowgen_contracts import (
    AssetKind,
    AssetRef,
    JobQueuedSignal,
    JobRealtimeEvent,
    JobRecord,
    JobStatus,
    JobTraceStage,
    ProcessingMetrics,
    RealtimeSubscription,
    RenderRequest,
    RenderResult,
    WorkerHeartbeatMessage,
    derive_job_timing_metrics,
)


def test_realtime_subscription_and_event_contracts_are_serializable() -> None:
    now = datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc)

    subscription = RealtimeSubscription(
        base_url="https://rt.shadowgen.solofarm.ru",
        path="/v1/realtime/jobs/job-1/events",
        token="token",
        expires_at=now + timedelta(minutes=5),
    )
    event = JobRealtimeEvent(
        event_id="event-1",
        event_type="job_succeeded",
        job_id="job-1",
        status=JobStatus.SUCCEEDED,
        occurred_at=now,
        updated_at=now,
        source="worker",
        result_available=True,
        duration_ms=936,
    )

    assert subscription.model_dump(mode="json")["transport"] == "sse"
    assert subscription.model_dump(mode="json")["fallback_poll_ms"] == 350
    assert event.model_dump(mode="json")["status"] == "succeeded"
    assert event.model_dump(mode="json")["result_available"] is True


def test_queued_signal_rejects_non_queued_status() -> None:
    now = datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        JobQueuedSignal(
            event_id="event-1",
            job_id="job-1",
            status="succeeded",
            queued_at=now,
            idempotency_key="job-queued:job-1",
        )


def test_worker_heartbeat_uses_independent_in_flight_lists() -> None:
    now = datetime(2026, 6, 23, 12, 0, tzinfo=timezone.utc)

    first = WorkerHeartbeatMessage(worker_id="worker-1", sent_at=now)
    second = WorkerHeartbeatMessage(worker_id="worker-2", sent_at=now)
    first.in_flight_job_ids.append("job-1")

    assert first.in_flight_job_ids == ["job-1"]
    assert second.in_flight_job_ids == []


def test_derive_job_timing_metrics_from_authoritative_job_fields() -> None:
    created_at = datetime(2026, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
    worker_claimed_at = created_at + timedelta(milliseconds=150)
    started_at = created_at + timedelta(milliseconds=250)
    finished_at = created_at + timedelta(milliseconds=1250)

    worker_claimed = JobTraceStage(
        name="worker_claimed",
        status="succeeded",
        started_at=worker_claimed_at,
        finished_at=worker_claimed_at,
        duration_ms=0,
    )
    ml_poll = JobTraceStage(
        name="ml_poll",
        status="succeeded",
        started_at=started_at + timedelta(milliseconds=200),
        finished_at=started_at + timedelta(milliseconds=900),
        duration_ms=700,
    )
    result = RenderResult(
        images=[AssetRef(asset_id="asset-final", kind=AssetKind.FINAL, mime_type="image/png")],
        metrics=ProcessingMetrics(total_ms=600),
    )
    job = JobRecord(
        job_id="job-1",
        status=JobStatus.SUCCEEDED,
        request=RenderRequest(source_asset_id="asset-source"),
        created_at=created_at,
        updated_at=finished_at,
        started_at=started_at,
        finished_at=finished_at,
        result=result,
        trace=[worker_claimed, ml_poll],
    )

    timing = derive_job_timing_metrics(job)

    assert timing.queue_wait_ms == 150
    assert timing.pre_start_worker_ms == 100
    assert timing.worker_duration_ms == 1000
    assert timing.ml_total_ms == 600
    assert timing.worker_overhead_ms == 400
    assert timing.ml_poll_overhead_ms == 100
