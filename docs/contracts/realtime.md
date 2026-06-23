# Realtime Contract

## Status

Shared DTOs and the VPS realtime service are implemented. API queued notifications, browser SSE subscription metadata, browser SSE fallback, and worker lifecycle event publishing are wired behind `VPS_ACCELERATOR_ENABLED`.

Worker wake hints are not implemented yet. Executable work still comes from YMQ.

## Design Rule

Realtime is an accelerator only.

The durable path remains:

```text
browser -> web -> api -> Object Storage + YMQ -> worker -> ML core -> Object Storage -> api -> browser
```

Clients and workers must continue to operate when realtime metadata is absent or the future realtime endpoint is unavailable.

## Public Subscription Metadata

`POST /v1/jobs` and `GET /v1/jobs/{job_id}` may include:

```json
{
  "realtime": {
    "transport": "sse",
    "base_url": "https://rt.shadowgen.solofarm.ru",
    "path": "/v1/realtime/jobs/job-1/events",
    "token": "job-scoped-token",
    "expires_at": "2026-06-23T12:05:00Z",
    "fallback_poll_ms": 350
  }
}
```

Rules:

- the field is optional
- `transport` is currently `sse`
- token is job-scoped and short-lived
- subscription metadata does not grant result access or mutation rights
- result and artifact reads still go through the public API

## Job Events

Shared event schema:

```json
{
  "event_version": "1",
  "event_id": "event-1",
  "event_type": "job_succeeded",
  "job_id": "job-1",
  "status": "succeeded",
  "occurred_at": "2026-06-23T12:00:01Z",
  "updated_at": "2026-06-23T12:00:01Z",
  "source": "worker",
  "sequence": 3,
  "result_available": true,
  "duration_ms": 936
}
```

Supported event types:

- `connected`
- `job_queued`
- `job_running`
- `job_worker_seen`
- `job_succeeded`
- `job_failed`
- `job_canceled`
- `keepalive`
- `fallback_required`

Allowed event sources:

- `api`
- `worker`
- `vps`

Events must not contain image bytes, artifact bytes, storage credentials, admin tokens, worker control tokens, or private ML details.

## API To VPS Queued Signal

Internal endpoint:

```http
POST /internal/v1/jobs/queued
Authorization: Bearer <VPS_INTERNAL_TOKEN>
```

Payload contract:

```json
{
  "message_version": "1",
  "event_id": "event-1",
  "job_id": "job-1",
  "status": "queued",
  "cache_status": "miss",
  "reused_existing_job": false,
  "queued_at": "2026-06-23T12:00:00Z",
  "idempotency_key": "job-queued:job-1"
}
```

Response contract:

```json
{
  "accepted": true,
  "duplicate": false
}
```

The API must call this only after durable job creation and queue publish succeed, and future notifier failures must not fail `POST /v1/jobs`.

## Worker To VPS Job Event

Internal endpoint:

```http
POST /internal/v1/jobs/events
Authorization: Bearer <WORKER_VPS_TOKEN>
```

Payload contract:

```json
{
  "event_version": "1",
  "event_id": "event-2",
  "event_type": "job_succeeded",
  "job_id": "job-1",
  "status": "succeeded",
  "occurred_at": "2026-06-23T12:00:01Z",
  "updated_at": "2026-06-23T12:00:01Z",
  "source": "worker",
  "worker_id": "local-gpu-1",
  "result_available": true,
  "duration_ms": 936
}
```

Response contract:

```json
{
  "accepted": true,
  "duplicate": false
}
```

The worker publishes these events only after the durable job state update path has run. Publishing failures are best-effort and must not fail a job.

## Worker Messages

Worker hello:

```json
{
  "message_version": "1",
  "message_type": "worker_hello",
  "worker_id": "local-gpu-1",
  "started_at": "2026-06-23T12:00:00Z",
  "max_in_flight_jobs": 4,
  "async_enabled": true,
  "mode": "async"
}
```

Worker heartbeat:

```json
{
  "message_version": "1",
  "message_type": "worker_heartbeat",
  "worker_id": "local-gpu-1",
  "sent_at": "2026-06-23T12:00:05Z",
  "in_flight_job_ids": ["job-1"]
}
```

Worker job event:

```json
{
  "message_version": "1",
  "message_type": "worker_job_event",
  "event_id": "event-2",
  "worker_id": "local-gpu-1",
  "job_id": "job-1",
  "event_type": "job_succeeded",
  "status": "succeeded",
  "occurred_at": "2026-06-23T12:00:01Z",
  "result_available": true,
  "duration_ms": 936
}
```

Worker wake command:

```json
{
  "message_version": "1",
  "message_type": "job_wake",
  "command_id": "command-1",
  "job_id": "job-1",
  "queued_at": "2026-06-23T12:00:00Z"
}
```

MVP wake rule:

- the wake command may wake the worker loop
- executable work must still come from YMQ
- direct execution by `job_id` remains out of scope until a durable claim/lease contract exists
- current implementation has not enabled the wake command transport yet
