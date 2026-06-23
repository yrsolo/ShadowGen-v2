from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx

from shadowgen_contracts import JobQueuedSignal, JobRecord, JobStatus, JobRealtimeEvent, RealtimeSubscription

from .signing import sign_job_token


class NullRealtimeAccelerator:
    def subscription_for_job(self, job_id: str) -> RealtimeSubscription | None:
        return None

    def notify_job_queued(self, job: JobRecord) -> None:
        return None

    def notify_job_event(self, event: JobRealtimeEvent) -> None:
        return None


class HttpRealtimeAccelerator:
    def __init__(
        self,
        base_url: str,
        internal_token: str,
        signing_secret: str,
        timeout_ms: int = 300,
        token_ttl_sec: int = 300,
        fallback_poll_ms: int = 350,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.internal_token = internal_token
        self.signing_secret = signing_secret
        self.timeout_sec = max(1, timeout_ms) / 1000
        self.token_ttl_sec = max(1, token_ttl_sec)
        self.fallback_poll_ms = max(50, fallback_poll_ms)

    def subscription_for_job(self, job_id: str) -> RealtimeSubscription | None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.token_ttl_sec)
        token = sign_job_token(job_id=job_id, expires_at=expires_at, secret=self.signing_secret)
        return RealtimeSubscription(
            base_url=self.base_url,
            path=f"/v1/realtime/jobs/{job_id}/events",
            token=token,
            expires_at=expires_at,
            fallback_poll_ms=self.fallback_poll_ms,
        )

    def notify_job_queued(self, job: JobRecord) -> None:
        if job.status != JobStatus.QUEUED or job.reused_existing_job:
            return
        signal = JobQueuedSignal(
            event_id=str(uuid4()),
            job_id=job.job_id,
            cache_status=job.cache_status,
            reused_existing_job=job.reused_existing_job,
            queued_at=job.created_at,
            idempotency_key=f"job-queued:{job.job_id}",
        )
        self._post("/internal/v1/jobs/queued", signal.model_dump(mode="json"))

    def notify_job_event(self, event: JobRealtimeEvent) -> None:
        self._post("/internal/v1/jobs/events", event.model_dump(mode="json"))

    def _post(self, path: str, payload: dict) -> None:
        response = httpx.post(
            f"{self.base_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self.internal_token}"},
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
