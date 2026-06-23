# VPS Accelerator Architecture Plan

## Status

Planning document with Phase 1 contracts, Phase 2 realtime service, Phase 3 API notifier, Phase 4 browser SSE fallback, Phase 5 worker lifecycle event publishing, and Phase 6 worker wake hints implemented.

## Why Add A VPS Layer

The current production-shaped path is intentionally durable:

```text
browser -> web -> api -> Object Storage + YMQ -> worker -> ML core -> Object Storage -> api -> browser
```

This shape is robust, but fast jobs expose fixed overhead:

- the browser observes completion through repeated API polling
- the API has no push channel to tell the worker that a new job arrived
- the worker can still be between queue receive cycles after an empty receive
- job and artifact state is read through Object Storage-backed API calls
- client time includes upload/create/result observation, while worker logs measure a narrower interval

The VPS should therefore be a low-latency accelerator, not the first source of truth.

## Design Principle

The first VPS version must be optional.

If the VPS is unavailable:

- `POST /v1/jobs` still creates the durable job record
- the job is still published to YMQ
- the worker still consumes YMQ
- the worker still writes result artifacts and metadata to Object Storage
- the browser still polls `GET /v1/jobs/{job_id}`

No user job may be lost because a VPS request, SSE stream, or WebSocket connection failed.

## Target Runtime Shape

```text
                         best-effort notify
browser -> web -> api ---------------------------> VPS accelerator
   |        |     |                                 |    |
   |        |     +-> Object Storage + YMQ          |    |
   |        |                                       |    |
   |        +----------- optional SSE --------------+    |
   |                                                     |
   +-------------- fallback API polling -----------------+

worker -> YMQ + Object Storage
worker <---------- optional wake/events ----------> VPS accelerator
worker -> ML core
```

The durable path remains the same. The VPS adds:

1. Browser realtime events, so the browser can stop waiting for the next polling tick.
2. Worker wake signals, so a worker can immediately return to queue receive after an API-created job.
3. Optional transient event buffering, so short client reconnects do not lose the latest status.

## Non-Goals For The First VPS Phase

- No image upload through the VPS.
- No final artifact proxy through the VPS.
- No replacement of YMQ with an in-memory queue.
- No direct worker execution from a `job_id` unless a separate durable claim/lease contract is added.
- No public exposure of worker control endpoints.
- No application/domain dependency on HTTP, SSE, WebSocket, Redis, or VPS-specific libraries.

## Component Responsibilities

### `apps/api`

API stays the durable command entrypoint.

Responsibilities:

- validate source assets and create jobs through the existing use case
- write job state to the configured job repository
- publish `RenderJobQueuedMessage` to the configured queue
- after durable create and queue publish, send a best-effort queued signal to the VPS
- include optional realtime subscription information in job responses
- never fail job creation because VPS notification failed

VPS calls from API must be short-timeout and circuit-breakered.

### `apps/web`

Web remains a public API client.

Responsibilities:

- continue to create assets and jobs through the public API
- if a realtime subscription is returned, open an SSE stream
- keep API polling as fallback
- on terminal realtime event, verify by fetching the job or result through the API
- expose timing diagnostics that separate:
  - create-job latency
  - realtime event latency
  - fallback polling latency
  - result image visible latency

### `apps/worker`

Worker remains the durable executor.

Responsibilities:

- keep the YMQ receive loop as the source of executable work
- keep queue visibility extension and ack/nack behavior
- maintain an optional outbound connection to the VPS
- publish worker-side status events after durable state updates
- treat VPS wake commands as wake-up hints, not as a replacement queue

For the MVP, a wake command should only interrupt worker sleep and prompt the worker to receive from YMQ. It should not bypass YMQ by directly executing the job id.

### New `apps/vps` Or `apps/realtime`

Recommended name: `apps/realtime`.

Responsibilities:

- expose public read-only browser event streams for specific jobs
- expose internal API-to-VPS event ingestion
- expose internal worker connection/event ingestion
- authenticate internal callers
- authorize browser subscriptions with short-lived tokens
- hold transient event buffers in memory, or Redis if configured
- publish health/metrics endpoints

It should not know ML-core details, render settings, or asset bytes.

### `packages/contracts`

Add explicit DTOs for the accelerator boundary.

Suggested file:

```text
packages/contracts/src/shadowgen_contracts/realtime.py
```

This file should define only schema contracts and enums. No HTTP client code.

### `packages/application`

Add ports only when use cases need to emit accelerator events.

Candidate ports:

```python
class JobEventPublisherPort(Protocol):
    def publish(self, event: JobRealtimeEvent) -> None:
        ...

class WorkerWakePublisherPort(Protocol):
    def notify_job_queued(self, signal: JobQueuedSignal) -> None:
        ...
```

Keep these ports generic. Do not name them after VPS, HTTP, SSE, or WebSocket in the application layer.

### `packages/adapters`

Add infrastructure implementations:

```text
packages/adapters/src/shadowgen_adapters/realtime/
  http_event_publisher.py
  null_event_publisher.py
  signing.py
```

The API and worker composition layers choose real or null adapters from config.

## First Architecture Choice

### Recommended MVP

Use the VPS for:

- public browser SSE
- internal best-effort status ingestion
- internal worker wake hints

Do not use the VPS as a queue.

Reason:

- the current queue already has delivery, visibility, retry, and ack/nack semantics
- S3/Object Storage job metadata is not a good compare-and-swap lock by itself
- direct job-id execution can duplicate work if YMQ redelivers, if multiple workers are added, or if a worker crashes after starting ML work
- a wake hint can reduce idle delay without changing correctness semantics

## Contract Overview

### Public Job Response Extension

Extend `CreateJobResponse` and optionally `GetJobResponse` with realtime metadata.

Proposed optional field:

```json
{
  "realtime": {
    "transport": "sse",
    "base_url": "https://rt.shadowgen.solofarm.ru",
    "path": "/v1/realtime/jobs/{job_id}/events",
    "token": "<short-lived-browser-token>",
    "expires_at": "2026-06-23T12:00:00Z",
    "fallback_poll_ms": 350
  }
}
```

Rules:

- field is optional
- old web clients continue to work
- web ignores it if missing, expired, or failed
- token is job-scoped and short-lived
- token authorizes event observation only, not result access
- result and artifact access still goes through the API

Suggested contract type:

```python
class RealtimeSubscription(BaseModel):
    transport: Literal["sse"]
    base_url: str
    path: str
    token: str
    expires_at: datetime
    fallback_poll_ms: int = 350
```

### Browser SSE Endpoint

Endpoint:

```http
GET /v1/realtime/jobs/{job_id}/events?token=<token>&last_event_id=<event_id>
Accept: text/event-stream
```

Response event format:

```text
id: <event_id>
event: job_succeeded
data: {"event_version":"1","event_id":"...","event_type":"job_succeeded","job_id":"...","status":"succeeded","occurred_at":"...","source":"worker","result_available":true}
```

Supported event names:

- `connected`
- `job_queued`
- `job_running`
- `job_worker_seen`
- `job_succeeded`
- `job_failed`
- `job_canceled`
- `keepalive`
- `fallback_required`

Client behavior:

- on `connected`, keep current API polling active until a useful job event arrives
- on `job_queued` or `job_running`, update local status only
- on terminal event, call the API once to fetch authoritative job/result state
- if stream closes, returns unauthorized, or receives `fallback_required`, keep polling
- if event order is unclear, prefer the newest API state

### Realtime Event DTO

Proposed schema:

```python
class JobRealtimeEvent(BaseModel):
    event_version: Literal["1"] = "1"
    event_id: str
    event_type: Literal[
        "connected",
        "job_queued",
        "job_running",
        "job_worker_seen",
        "job_succeeded",
        "job_failed",
        "job_canceled",
        "keepalive",
        "fallback_required",
    ]
    job_id: str
    status: JobStatus | None = None
    occurred_at: datetime
    updated_at: datetime | None = None
    source: Literal["api", "worker", "vps"]
    sequence: int | None = None
    cache_status: str | None = None
    reused_existing_job: bool | None = None
    worker_id: str | None = None
    result_available: bool = False
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
```

Rules:

- `event_id` is globally unique for idempotency
- `sequence` is optional at first, but useful once the VPS keeps per-job order
- `result_available=true` means the browser should fetch authoritative state from the API
- events do not contain image bytes, signed artifact URLs, source bytes, or storage credentials

### API To VPS Queued Signal

Endpoint:

```http
POST /internal/v1/jobs/queued
Authorization: Bearer <VPS_INTERNAL_TOKEN>
Content-Type: application/json
```

Payload:

```json
{
  "message_version": "1",
  "event_id": "1c8e7e52-8d25-4b88-8ec8-1d6f3b9a1fd1",
  "job_id": "66c8b721-c004-4590-be67-0ddaceb28510",
  "status": "queued",
  "cache_status": "miss",
  "reused_existing_job": false,
  "queued_at": "2026-06-23T11:35:03Z",
  "idempotency_key": "job-queued:66c8b721-c004-4590-be67-0ddaceb28510"
}
```

Response:

```json
{
  "accepted": true,
  "duplicate": false
}
```

Rules:

- API calls this only after job repository create and queue publish succeeded
- API timeout should be low, suggested `200-500 ms`
- API logs failures but does not fail the public request
- VPS deduplicates by `event_id` and `idempotency_key`
- VPS publishes a browser `job_queued` event and a worker `job_wake` command

### Worker To VPS Connection

Recommended MVP: one outbound WebSocket from worker to VPS.

Endpoint:

```http
GET /internal/v1/workers/{worker_id}/connect
Authorization: Bearer <WORKER_VPS_TOKEN>
```

Worker hello:

```json
{
  "message_version": "1",
  "message_type": "worker_hello",
  "worker_id": "local-gpu-1",
  "started_at": "2026-06-23T11:35:00Z",
  "max_in_flight_jobs": 4,
  "capabilities": {
    "async_enabled": true,
    "mode": "async"
  }
}
```

Heartbeat:

```json
{
  "message_version": "1",
  "message_type": "worker_heartbeat",
  "worker_id": "local-gpu-1",
  "sent_at": "2026-06-23T11:35:05Z",
  "in_flight_job_ids": ["66c8b721-c004-4590-be67-0ddaceb28510"]
}
```

Worker job event:

```json
{
  "message_version": "1",
  "message_type": "worker_job_event",
  "event_id": "0ebf1d88-9351-438d-bd1b-48f955db37cc",
  "worker_id": "local-gpu-1",
  "job_id": "66c8b721-c004-4590-be67-0ddaceb28510",
  "event_type": "job_succeeded",
  "status": "succeeded",
  "occurred_at": "2026-06-23T11:35:06Z",
  "result_available": true,
  "duration_ms": 936
}
```

VPS wake command to worker:

```json
{
  "message_version": "1",
  "message_type": "job_wake",
  "command_id": "b2dbd3e1-8117-4b6f-91dc-b0d3cc98030d",
  "job_id": "66c8b721-c004-4590-be67-0ddaceb28510",
  "queued_at": "2026-06-23T11:35:03Z"
}
```

MVP worker rule:

- receiving `job_wake` sets a local wake event
- the worker loop immediately calls `queue.receive()`
- actual executable work still comes from YMQ
- if YMQ has not exposed the message yet, the worker returns to normal long polling

### Worker Terminal Event Ordering

The worker should send `job_succeeded` or `job_failed` only after it has updated the durable job record.

Sequence:

```text
worker finishes ML
worker stores artifact bytes
worker updates durable JobRecord to terminal status
worker emits VPS event
VPS emits SSE terminal event
browser fetches authoritative API job/result
```

This prevents the browser from seeing a terminal event before the API can serve the result.

## Fallback Matrix

| Failure | Expected behavior |
| --- | --- |
| VPS down during `POST /v1/jobs` | API logs notify failure, job remains queued in YMQ, browser polls API |
| Browser SSE fails | UI keeps API polling, no job loss |
| Worker WebSocket disconnected | Worker keeps YMQ polling, VPS may only serve API-origin queued events |
| API-to-VPS token invalid | API notify fails closed, durable path continues |
| Worker token invalid | Worker is not accelerated, YMQ path continues |
| VPS restarts | In-memory event buffer is lost, clients reconnect and poll API |
| Duplicate queued signal | VPS deduplicates; YMQ and job terminal no-op still protect the durable path |
| Out-of-order events | Browser treats API job fetch as authoritative |

## Security Model

### Public Browser Access

- Browser uses a short-lived job-scoped token.
- Token grants read access only to one job event stream.
- Token does not grant access to artifacts or job mutation endpoints.
- CORS should allow only:
  - `https://shadowgen.solofarm.ru`
  - local development origins
- SSE endpoint should reject unknown origins in production.

### Internal API And Worker Access

MVP can use static bearer tokens:

- `VPS_INTERNAL_TOKEN` for API-to-VPS notifications
- `WORKER_VPS_TOKEN` for worker-to-VPS connection

Later hardening:

- HMAC signatures over request body and timestamp
- token rotation
- per-worker tokens
- request timestamp freshness window
- IP allowlist if the VPS networking makes that practical

### Data Minimization

The VPS must not receive:

- source image bytes
- final artifact bytes
- S3/YMQ credentials
- admin API token
- worker control token
- private ML URL unless needed for diagnostics, and it is not needed in MVP

## Environment Variables

### API

```dotenv
VPS_ACCELERATOR_ENABLED=false
VPS_ACCELERATOR_URL=https://rt.shadowgen.solofarm.ru
VPS_INTERNAL_TOKEN=
VPS_NOTIFY_TIMEOUT_MS=300
VPS_NOTIFY_CIRCUIT_OPEN_SEC=30
VPS_REALTIME_TOKEN_TTL_SEC=300
```

### Web

If the API returns absolute realtime URLs, web may not need a new variable.

Optional:

```dotenv
NEXT_PUBLIC_REALTIME_BASE=https://rt.shadowgen.solofarm.ru
```

### Worker

```dotenv
VPS_ACCELERATOR_ENABLED=false
VPS_ACCELERATOR_URL=https://rt.shadowgen.solofarm.ru
WORKER_ID=local-gpu-1
WORKER_VPS_TOKEN=
VPS_WAKE_ENABLED=true
VPS_EVENT_TIMEOUT_MS=300
VPS_RECONNECT_MIN_SEC=1
VPS_RECONNECT_MAX_SEC=30
```

### VPS

```dotenv
APP_ENV=prod
VPS_PUBLIC_BASE_URL=https://rt.shadowgen.solofarm.ru
VPS_INTERNAL_TOKEN=
WORKER_VPS_TOKEN=
ALLOWED_ORIGINS=https://shadowgen.solofarm.ru,http://localhost:3000,http://127.0.0.1:3000
EVENT_RETENTION_SEC=300
HEARTBEAT_INTERVAL_SEC=15
REDIS_URL=
```

## Observability

Add or expose these timing fields before relying on the accelerator:

- `queue_wait_ms = worker_claimed.started_at - job.created_at`
- `pre_start_worker_ms = job.started_at - worker_claimed.started_at`
- `worker_duration_ms = job.finished_at - job.started_at`
- `ml_total_ms = job.result.metrics.total_ms`
- `worker_overhead_ms = worker_duration_ms - ml_total_ms`
- `ml_poll_overhead_ms = ml_poll.duration_ms - ml_total_ms`
- `api_to_vps_notify_ms`
- `vps_to_worker_wake_ms`
- `worker_terminal_to_vps_ms`
- `vps_terminal_to_browser_ms`
- `browser_terminal_to_image_visible_ms`
- `sse_connected`
- `sse_fallback_reason`
- `api_poll_count`

These metrics should make it clear whether remaining delay is:

- browser upload
- API create
- queue pickup
- worker processing
- artifact storage
- browser result fetch
- image decode/render

## Implementation Phases

### Phase 0: Instrument Before Infrastructure

Goal: make baseline measurements unambiguous.

Tasks:

- add backend-derived `queue_wait_ms`, `worker_duration_ms`, `worker_overhead_ms`, and `ml_poll_overhead_ms` to diagnostics or engineering UI
- add client-side `job_terminal_observed_at` and `image_visible_at`
- record whether terminal status was observed through polling or realtime
- confirm current queue idle sleep and YMQ receive behavior in tests

Checks:

- unit tests for timing derivation from `JobRecord.trace`
- web build
- docs check

Rollback:

- remove UI-only timing display without changing runtime behavior

### Phase 1: Shared Contracts

Goal: define DTOs without VPS runtime behavior.

Status: implemented for shared DTOs, optional response metadata, TypeScript types, and derived API timing metrics.

Tasks:

- add `RealtimeSubscription` to contracts - done
- add `JobRealtimeEvent`, `JobQueuedSignal`, worker message DTOs - done
- extend Python exports from `shadowgen_contracts.__init__` - done
- extend TypeScript web types - done
- document that all fields are optional until backend support is enabled - done
- expose response-only derived timing metrics in create/get job responses - done

Checks:

- Python import/unit tests for DTO validation
- TypeScript build
- architecture boundary tests

Rollback:

- contracts are additive and optional

### Phase 2: VPS Realtime Service Skeleton

Goal: deploy a no-risk service with health and event fan-out.

Status: implemented as `apps/realtime` with Dockerfile and VPS deploy script. The service is intentionally disconnected from API/web/worker until later phases.

Tasks:

- create `apps/realtime` - done
- implement `GET /health` - done
- implement `GET /v1/realtime/jobs/{job_id}/events` - done
- implement internal `POST /internal/v1/jobs/queued` - done
- implement in-memory per-job event buffer with retention - done
- implement public token verification - done
- implement internal bearer token auth - done
- add Dockerfile and VPS deploy script - done
- add deployment notes for Docker on VPS - done

Checks:

- unit tests for auth, event buffer, and SSE formatting
- integration test using FastAPI `TestClient` or `httpx`
- docs check

Rollback:

- do not point API/web/worker at this service until later phases

### Phase 3: API Best-Effort Notifier

Goal: notify VPS after durable job creation.

Status: implemented for queued notifications and job-scoped subscription metadata.

Tasks:

- add config values to `ApiConfig` - done
- add composition-level realtime accelerator adapter - done
- implement HTTP and null accelerator adapters - done
- call notifier after `CreateJobUseCase.execute()` returns - done
- generate browser subscription metadata when enabled - done
- include optional `realtime` in `CreateJobResponse` and `GetJobResponse` - done
- add short timeout - done

Important rule:

- durable create and YMQ publish happen first
- notifier failure is swallowed and logged

Checks:

- test create job succeeds when notifier times out
- test notifier is not called before durable create
- test response remains backward-compatible when realtime disabled
- API integration tests

Rollback:

- set `VPS_ACCELERATOR_ENABLED=false`

### Phase 4: Browser SSE With Polling Fallback

Goal: reduce terminal observation delay.

Status: implemented in the web job lifecycle with API polling fallback.

Tasks:

- open SSE only when `CreateJobResponse.realtime` is present - done
- keep current API polling as fallback - done
- on terminal event, fetch authoritative job/result once - done
- show diagnostics: `observed_via=realtime|polling` - done
- handle stream close/error with fallback polling - done

Checks:

- component/unit tests for fallback state machine where feasible
- browser build
- manual smoke:
  - realtime enabled and VPS healthy
  - VPS disabled
  - VPS killed during job

Rollback:

- ignore `realtime` field or disable with env

### Phase 5: Worker Event Publishing

Goal: let worker terminal status reach browser without waiting for API polling.

Status: implemented with HTTP event publishing.

Tasks:

- add worker config values - done
- post lifecycle events by HTTP - done
- emit `job_worker_seen` after worker submit/claim path - done
- emit `job_succeeded` after durable terminal update path - done
- emit `job_failed` after durable failure update path - done
- keep events best-effort - done
- reconnect with exponential backoff - not needed for HTTP-only event publishing

Checks:

- tests for observer dispatch order: durable update before event publish
- tests for event publisher failure not failing job
- worker loop resilience tests

Rollback:

- set `VPS_ACCELERATOR_ENABLED=false` for worker only

### Phase 6: Worker Wake Hints

Goal: reduce queue pickup delay while preserving YMQ correctness.

Status: implemented with worker outbound SSE wake stream and local `threading.Event` wake.

Tasks:

- extend the worker loop with a `threading.Event` or equivalent wake primitive - done
- make VPS `job_wake` command set that event - done
- when awakened, the worker immediately calls `queue.receive()` - done
- keep normal `queue.receive()` and sleep behavior if no wake arrives - done
- do not direct-execute `job_id` - done
- add metrics for wake commands received and wake-to-receive latency - pending

Checks:

- unit test: wake interrupts idle sleep
- unit test: duplicate wake does not duplicate execution
- unit test: YMQ delivery still required for execution
- integration test with fake VPS

Rollback:

- disable `VPS_WAKE_ENABLED`

### Phase 7: Optional Redis Buffer

Goal: survive VPS process restarts and support more reliable reconnects.

Only do this if in-memory buffering proves insufficient.

Tasks:

- add `REDIS_URL`
- store recent events per job with TTL
- keep worker connection registry in memory, not necessarily Redis
- support `Last-Event-ID` replay for browser reconnects

Checks:

- Redis-backed buffer tests
- restart/reconnect smoke

Rollback:

- unset `REDIS_URL` and return to memory buffer

### Phase 8: Optional Durable Fast State

Goal: reduce Object Storage metadata reads only if measured as a major remaining cost.

This is a larger design step and should not be mixed with the MVP.

Candidate options:

- Redis cache with Object Storage as source of truth
- Postgres metadata store
- YDB or another cloud database with conditional writes

Required before direct job execution:

- explicit conditional job claim
- lease owner and lease expiration fields
- idempotent completion
- recovery of abandoned running jobs
- duplicate YMQ delivery behavior

Without these semantics, keep direct execution out of scope.

## Repository Task Breakdown

### Contracts

- add `packages/contracts/src/shadowgen_contracts/realtime.py`
- export DTOs from `packages/contracts/src/shadowgen_contracts/__init__.py`
- add optional `realtime` to `CreateJobResponse`
- add matching TypeScript types in `apps/web/src/lib/types.ts`
- update `docs/contracts/jobs.md` or add `docs/contracts/realtime.md` after implementation starts

### API

- add VPS config to `apps/api/src/shadowgen_api/config.py`
- add notifier dependency wiring in `apps/api/src/shadowgen_api/deps.py`
- call notifier in job create route or use-case composition
- add tests for disabled/notifier-failing modes

### Worker

- add VPS config to `apps/worker/src/shadowgen_worker/config.py`
- add optional realtime client in worker composition
- add wake primitive to `WorkerLoop`
- extend worker observer to publish status events
- add tests for wake and best-effort event failures

### VPS App

- create `apps/realtime`
- add FastAPI app
- add Dockerfile
- add service config
- add auth helpers
- add event buffer
- add SSE endpoint
- add internal ingestion endpoints
- add worker connection endpoint

### Web

- add SSE client helper
- integrate with current job lifecycle state machine
- keep polling fallback
- add realtime timing diagnostics
- add build/test coverage for type changes

### Docs And Ops

- add deployment guide for VPS accelerator after implementation
- update runtime topology after first phase is deployed
- add env examples after config is implemented
- add failure drills to evidence before rollout

## Deployment Plan

1. Deploy VPS service with only `/health`.
2. Enable internal endpoints but keep API/worker disabled.
3. Enable API best-effort notifications in staging/local only.
4. Enable browser SSE with fallback.
5. Enable worker terminal events.
6. Enable worker wake hints.
7. Observe metrics for at least several real jobs.
8. Roll out to production by toggling env flags, not by requiring a code rollback.

## Rollback Plan

Immediate rollback:

```dotenv
VPS_ACCELERATOR_ENABLED=false
```

Partial rollback:

```dotenv
VPS_WAKE_ENABLED=false
```

Expected rollback result:

- browser returns to API polling
- worker returns to YMQ polling
- API keeps durable job creation
- no queued job is stranded

## Success Criteria

Functional:

- every job still completes with VPS disabled
- API create-job success rate does not depend on VPS health
- browser can observe terminal state through realtime when enabled
- browser still observes terminal state through polling when realtime fails
- worker wake hints never bypass YMQ in the MVP

Latency:

- terminal-observation delay drops from polling quantum plus API read to near one SSE event delivery
- worker queue pickup delay after an API-created job drops when worker is idle
- no regression in ML processing or artifact storage duration

Operational:

- clear health endpoint for VPS
- metrics show realtime usage and fallback rate
- tokens are not exposed in logs
- deployment can be disabled with env only

## Open Decisions

1. Service name: `apps/realtime` is clearer than `apps/vps` because the app role is realtime acceleration, not all VPS work.
2. Browser token signing: reuse API secret-derived HMAC or create a separate `VPS_REALTIME_SIGNING_SECRET`.
3. Worker connection: WebSocket is best for wake hints; HTTP-only is simpler for terminal event publishing but cannot wake the worker.
4. Event buffer: start in memory; add Redis only after reconnect/restart behavior needs it.
5. Public hostname: likely `rt.shadowgen.solofarm.ru`, but this belongs in deployment config.

## Implementation Order Recommendation

Do not start with direct queue replacement.

Start in this order:

1. contracts and metrics
2. VPS health/SSE/event buffer
3. API best-effort queued notifications
4. browser SSE fallback
5. worker terminal events
6. worker wake hints
7. optional Redis
8. optional durable fast metadata/claim store

This order gives measurable latency improvement while keeping each step independently reversible.
