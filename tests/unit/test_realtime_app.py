from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from shadowgen_realtime.auth import sign_job_token, verify_job_token
from shadowgen_realtime.main import create_app


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv("VPS_INTERNAL_TOKEN", "internal-token")
    monkeypatch.setenv("WORKER_VPS_TOKEN", "worker-token")
    monkeypatch.setenv("VPS_REALTIME_SIGNING_SECRET", "signing-secret")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return TestClient(create_app())


def test_health_reports_ok(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "shadowgen-realtime"


def test_internal_queued_endpoint_requires_bearer_token(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.post(
        "/internal/v1/jobs/queued",
        json={
            "event_id": "event-1",
            "job_id": "job-1",
            "queued_at": "2026-06-23T12:00:00Z",
            "idempotency_key": "job-queued:job-1",
        },
    )

    assert response.status_code == 401


def test_internal_queued_endpoint_publishes_and_deduplicates(monkeypatch) -> None:
    client = _client(monkeypatch)
    queued_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "event_id": "event-1",
        "job_id": "job-1",
        "status": "queued",
        "cache_status": "miss",
        "reused_existing_job": False,
        "queued_at": queued_at,
        "idempotency_key": "job-queued:job-1",
    }

    first = client.post(
        "/internal/v1/jobs/queued",
        json=payload,
        headers={"Authorization": "Bearer internal-token"},
    )
    second = client.post(
        "/internal/v1/jobs/queued",
        json=payload,
        headers={"Authorization": "Bearer internal-token"},
    )

    assert first.status_code == 200
    assert first.json() == {"accepted": True, "duplicate": False}
    assert second.status_code == 200
    assert second.json() == {"accepted": True, "duplicate": True}
    assert client.get("/health").json()["jobs_with_events"] == 1


def test_worker_event_endpoint_requires_worker_token(monkeypatch) -> None:
    client = _client(monkeypatch)
    payload = {
        "event_id": "event-worker-1",
        "event_type": "job_succeeded",
        "job_id": "job-1",
        "status": "succeeded",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "source": "worker",
        "worker_id": "worker-1",
        "result_available": True,
    }

    denied = client.post(
        "/internal/v1/jobs/events",
        json=payload,
        headers={"Authorization": "Bearer internal-token"},
    )
    accepted = client.post(
        "/internal/v1/jobs/events",
        json=payload,
        headers={"Authorization": "Bearer worker-token"},
    )

    assert denied.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json() == {"accepted": True, "duplicate": False}


def test_job_token_is_job_scoped_and_expires() -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = sign_job_token("job-1", expires_at, "signing-secret")

    verify_job_token(token, "job-1", "signing-secret")

    expired = sign_job_token("job-1", datetime.now(timezone.utc) - timedelta(seconds=1), "signing-secret")
    response_error = None
    try:
        verify_job_token(expired, "job-1", "signing-secret")
    except Exception as exc:
        response_error = exc
    assert response_error is not None
