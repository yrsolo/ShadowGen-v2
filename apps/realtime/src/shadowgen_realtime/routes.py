from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from shadowgen_contracts import (
    JobWakeCommand,
    JobQueuedSignal,
    JobRealtimeEvent,
    RealtimeAcceptedResponse,
)

from shadowgen_realtime.auth import assert_origin_allowed, require_bearer_token, verify_job_token
from shadowgen_realtime.events import encode_keepalive, encode_sse, encode_wake_sse

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    buffer = request.app.state.event_buffer
    return {
        "status": "ok",
        "service": "shadowgen-realtime",
        "jobs_with_events": await buffer.job_count(),
        "wake_commands": await request.app.state.wake_broker.command_count(),
    }


@router.post("/internal/v1/jobs/queued", response_model=RealtimeAcceptedResponse)
async def job_queued(
    signal: JobQueuedSignal,
    request: Request,
    authorization: str | None = Header(default=None),
):
    config = request.app.state.config
    require_bearer_token(authorization, config.vps_internal_token, "internal")
    event = JobRealtimeEvent(
        event_id=signal.event_id,
        event_type="job_queued",
        job_id=signal.job_id,
        status="queued",
        occurred_at=signal.queued_at,
        updated_at=signal.queued_at,
        source="api",
        cache_status=signal.cache_status,
        reused_existing_job=signal.reused_existing_job,
        result_available=False,
    )
    accepted = await request.app.state.event_buffer.publish(event)
    if accepted:
        await request.app.state.wake_broker.publish(
            JobWakeCommand(
                command_id=f"wake:{uuid4()}",
                job_id=signal.job_id,
                queued_at=signal.queued_at,
            )
        )
    return RealtimeAcceptedResponse(accepted=True, duplicate=not accepted)


@router.post("/internal/v1/jobs/events", response_model=RealtimeAcceptedResponse)
async def job_event(
    event: JobRealtimeEvent,
    request: Request,
    authorization: str | None = Header(default=None),
):
    config = request.app.state.config
    require_bearer_token(authorization, config.worker_vps_token, "worker")
    accepted = await request.app.state.event_buffer.publish(event)
    return RealtimeAcceptedResponse(accepted=True, duplicate=not accepted)


@router.get("/v1/realtime/jobs/{job_id}/events")
async def job_events(
    job_id: str,
    token: str,
    request: Request,
    last_event_id: str | None = None,
):
    config = request.app.state.config
    allowed_origins = [item.strip() for item in config.allowed_origins.split(",") if item.strip()]
    assert_origin_allowed(request, allowed_origins)
    verify_job_token(token=token, job_id=job_id, secret=config.vps_realtime_signing_secret)

    async def stream():
        connected = JobRealtimeEvent(
            event_id=f"connected:{uuid4()}",
            event_type="connected",
            job_id=job_id,
            occurred_at=datetime.now(timezone.utc),
            source="vps",
        )
        yield encode_sse(connected)
        cursor = last_event_id
        while True:
            events = await request.app.state.event_buffer.list_events(job_id, cursor)
            for event in events:
                cursor = event.event_id
                yield encode_sse(event)
            await request.app.state.event_buffer.wait_for_event(job_id, config.heartbeat_interval_sec)
            if not events:
                yield encode_keepalive()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/internal/v1/workers/{worker_id}/wake")
async def worker_wake_stream(
    worker_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
):
    config = request.app.state.config
    require_bearer_token(authorization, config.worker_vps_token, "worker")

    async def stream():
        cursor = await request.app.state.wake_broker.command_count()
        while True:
            cursor, commands = await request.app.state.wake_broker.wait_for_commands(cursor, config.heartbeat_interval_sec)
            for command in commands:
                yield encode_wake_sse(command)
            if not commands:
                yield encode_keepalive()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/internal/v1/token/jobs/{job_id}")
async def issue_debug_token(
    job_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
):
    config = request.app.state.config
    require_bearer_token(authorization, config.vps_internal_token, "internal")
    if config.app_env == "prod":
        raise HTTPException(status_code=404, detail="Not found.")
    from datetime import timedelta

    from shadowgen_realtime.auth import sign_job_token

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    return {
        "job_id": job_id,
        "token": sign_job_token(job_id=job_id, expires_at=expires_at, secret=config.vps_realtime_signing_secret),
        "expires_at": expires_at,
    }
