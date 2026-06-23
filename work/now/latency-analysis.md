# Latency Analysis

## Scope

This note maps the current render hot path to observed timings and lists optimization options for:

- the current serverless API + YMQ + Object Storage runtime
- an optional VPS-assisted accelerator that can fail back to the current path

The user-visible flow is currently:

```text
browser -> web -> API -> Object Storage + YMQ -> worker -> ML core -> Object Storage -> API -> browser
```

## Observed Timings

Live diagnostics on 2026-06-23 matched the supplied screenshots.

| job | UI timer | worker duration | ML total | worker overhead | ml_poll overhead |
| --- | ---: | ---: | ---: | ---: | ---: |
| `a40440b9-003b-4bd2-9a9d-90cd7d117127` | 5.05 s | 3508 ms | 1719 ms | 1789 ms | 665 ms |
| `7a7ac8f4-4ca1-4d73-b70f-b0af6bc04754` | 4.32 s | 2358 ms | 174 ms | 2184 ms | 1089 ms |
| `8c0d548f-0a57-4d17-ba59-48c940b9bc0a` | 6.15 s | 4613 ms | 2870 ms | 1743 ms | 644 ms |

Recent live diagnostics also showed:

| job | worker duration | ML total | ml_probe | asset bytes | ml_submit | ml_poll | artifact_store |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `8c0d548f-0a57-4d17-ba59-48c940b9bc0a` | 4613 | 2870 | 185 | 150 | 119 | 3514 | 251 |
| `7a7ac8f4-4ca1-4d73-b70f-b0af6bc04754` | 2358 | 174 | 228 | 178 | 109 | 1263 | 184 |
| `a40440b9-003b-4bd2-9a9d-90cd7d117127` | 3508 | 1719 | 215 | 168 | 152 | 2384 | 253 |
| `4d5336dc-5ef3-493c-b813-6f078779cff3` | 4788 | 2852 | 237 | 163 | 112 | 3583 | 250 |
| `efeee5f7-453a-497a-bca0-5c399d335924` | 1481 | 169 | 236 | 164 | 111 | 174 | 401 |
| `c85591df-6be0-47e9-96cd-a9ffbcca7033` | 3564 | 1740 | 180 | 192 | 112 | 2437 | 214 |

Across those six jobs:

- average worker overhead over ML `total_ms`: about 1798 ms
- average `ml_poll - total_ms`: about 638 ms, or about 765 ms excluding the one job where the first poll caught the completed result
- average `ml_probe`: about 214 ms
- average `asset_bytes_loaded`: about 169 ms
- average `ml_submit`: about 119 ms
- average `artifact_store`: about 259 ms

The second live diagnostics request timed out after 20 seconds. That is not on the user render hot path, but it confirms that Engineering diagnostics can be expensive because `S3JobRepository.list_recent()` lists job objects and then reads each job JSON.

## Why The UI Timer Is Larger Than Job Logs

The compact UI timer starts before upload/create-job work. In `apps/web/src/app/page.tsx`, `startedAt` is set before `ensureUploadedSourceAssetId()`, `createJob()`, and the initial `getJob()`. The timer stops when the browser observes a terminal job through API polling.

The Engineering card duration is different. It is `finished_at - started_at`, and `started_at` is set inside worker processing after the worker has already claimed the job and loaded the source asset reference. Therefore it excludes browser upload, API create-job, queue wait, initial polling, and some pre-start worker work.

This makes the current difference expected:

```text
UI timer =
  browser upload/reuse
  + API create job
  + YMQ/worker pickup
  + worker duration
  + browser polling detection delay

Engineering duration =
  worker started_at -> worker finished_at
```

## Current Bottlenecks

### 1. Worker-to-ML async polling quantum

`ProcessJobUseCase` sleeps `poll_interval_ms / 1000` after a queued/running ML response. This was the first implementation target; the worker default is now `POLL_INTERVAL_MS=200`.

For short jobs, the previous one-second interval added up to almost one second of detection delay. The live samples taken before this change showed `ml_poll` exceeding ML `total_ms` by 644-1089 ms in most jobs.

### 2. ML capability probe per business job

Before the current optimization pass, `build_worker_runtime()` created a new `MLCorePipelineAdapter` inside `use_case_factory()`. The adapter had an in-memory capability cache, but the cache was thrown away after each job because each job received a fresh adapter instance.

The live `ml_probe` cost was consistently about 180-237 ms. The worker now reuses one adapter per effective ML URL, so warm jobs can reuse the adapter capability cache until `CAPABILITIES_REFRESH_INTERVAL_SEC` expires or the effective ML URL changes.

### 3. Object Storage reads and writes in worker hot path

The worker:

- reads source asset metadata
- reads source bytes, which reads metadata again first
- writes job JSON many times during trace updates
- writes final asset bytes
- writes final asset metadata
- writes final job JSON

The measured `asset_bytes_loaded` is around 150-192 ms and `artifact_store` is around 184-401 ms. The gap between summed visible stage durations and worker duration also points to storage writes between stages.

### 4. API create/get sequence

The browser does `createJob()` and then immediately `getJob()`. The create route already has the job record, but the response only returns summary fields. Returning the `JobRecord` from create would remove one API call and one Object Storage job read on every miss.

### 5. Browser polling

The browser polls `GET /v1/jobs/{job_id}` every 350 ms. That adds an average terminal-detection delay of roughly 175 ms plus API/Object Storage latency. It also repeatedly reads the full job record, including result metadata once complete.

### 6. Queue idle loop

YMQ receive uses long polling, but after an empty tick the worker sleeps for `poll_interval_sec`, default 1 second. If a message arrives just after an empty receive returns, that sleep can add up to 1 second. Long polling already provides the main idle wait, so the extra sleep can be reduced.

### 7. Result image proxy path

The result image is fetched through API `/v1/assets/{asset_id}/content`. That route first reads asset metadata and then reads object bytes from Object Storage. The compact timer stops when the job is observed as succeeded, not when the image finishes loading, but this still affects perceived result paint time.

## Optimizations Without VPS

### Stage 1: Instrumentation and timer clarity

- Show separate values in UI: `click-to-job-visible`, `worker duration`, `ML total`, and `image visible`.
- Add computed backend fields or diagnostics rows:
  - `queue_wait_ms = worker_claimed.started_at - created_at`
  - `pre_start_worker_ms = started_at - worker_claimed.started_at`
  - `worker_overhead_ms = finished_at - started_at - result.metrics.total_ms`
  - `ml_poll_overhead_ms = ml_poll.duration_ms - result.metrics.total_ms`
- Keep the compact timer, but label it as end-to-end visible time if shown to users.

Impact: no speedup, but it prevents comparing different clocks.

### Stage 2: Reduce ML async polling delay

- Change `POLL_INTERVAL_MS` from 1000 to 200-250 for the first few seconds. Implemented as a 200 ms default for the local ML service.
- Use adaptive backoff: 100-250 ms for the first 5 seconds, 500 ms until 30 seconds, then 1000 ms.
- Better option if ML-core can support it: add long-poll semantics to `GET /v1/render/jobs/{id}?wait_ms=1000`, so the worker blocks until completion or timeout instead of sleeping locally.

Expected impact: often 500-900 ms faster for the current short async jobs.

Risk: more ML status requests unless adaptive or long-poll is used.

### Stage 3: Reuse ML capability cache across jobs

- Build one `MLCorePipelineAdapter` per effective ML URL and reuse it across `ProcessJobUseCase` instances. Implemented.
- Invalidate the adapter when runtime ML URL changes.
- Keep `CAPABILITIES_REFRESH_INTERVAL_SEC` as the normal refresh policy.

Expected impact: about 180-240 ms faster per warm job.

Risk: must handle runtime ML URL override changes cleanly.

### Stage 4: Reduce storage chatter in worker

- Avoid duplicate source metadata read: `get_ref()` followed by `get_bytes()` currently re-reads metadata. Add an internal asset metadata object or a `get_bytes_for_ref()` style port method.
- Buffer trace writes: write job state on externally meaningful transitions, and write the full final trace at completion/failure.
- Keep worker runtime state as the live progress surface while the job is running.
- Store final asset bytes and metadata in parallel, or remove the separate metadata read from the final content path by making final asset object keys derivable from asset IDs and carrying MIME type in job result.

Expected impact: likely several hundred ms across source load, artifact store, and unmeasured inter-stage writes.

Risk: fewer mid-stage updates in diagnostics unless worker state becomes the live progress source.

### Stage 5: Reduce API/browser round trips

- Return the full `JobRecord` in `CreateJobResponse`, or add `job` as an optional field, so the browser can skip the immediate `getJob()`.
- Add a lightweight `/v1/jobs/{id}/status` response for polling if full job records become large.
- Use `ETag`/`If-None-Match` or `updated_at` based conditional reads for polling.
- Return direct immutable final artifact URLs or short-lived signed URLs in the job result to avoid proxying final images through the API.

Expected impact: usually 100-400 ms from fewer API/Object Storage reads, plus better perceived image paint.

Risk: public artifact URL policy and cache invalidation must be explicit.

### Stage 6: Tune queue long polling

- Increase `QUEUE_POLL_WAIT_SEC` to 10-20 seconds.
- Reduce worker `POLL_INTERVAL_SEC` after an empty receive to 0-0.1 seconds.

Expected impact: removes up to 1 second worst-case idle sleep without increasing empty queue calls if long polling is used.

Risk: check YMQ max long-poll wait and shutdown behavior.

## VPS-Assisted Options

The VPS should be an accelerator, not the source of truth at first. The existing S3 + YMQ path should remain durable and sufficient.

### Option A: Realtime completion channel

Add a small VPS service that exposes SSE/WebSocket to the browser:

```text
browser --SSE/WS--> VPS realtime service
worker ----job done event----> VPS realtime service
browser --fallback polling--> cloud API
```

Flow:

1. Browser still creates jobs through the cloud API.
2. Browser subscribes to `job_id` events on the VPS.
3. Worker still writes final job state to Object Storage.
4. Worker also sends a best-effort completion event to the VPS.
5. Browser uses the event to fetch the final job/result immediately.
6. If the VPS connection fails, browser keeps the current 350 ms API polling.

Expected impact: removes browser polling detection delay and improves perceived responsiveness. It does not fix worker-side `ml_poll` delay.

Fallback: automatic, because polling remains active.

### Option B: Best-effort wake signal for new jobs

Add a VPS job signal path:

```text
API durable path: create job -> Object Storage -> YMQ
API accelerator path: best-effort POST job_id -> VPS -> worker connection
worker fallback: normal YMQ loop
```

Flow:

1. API writes job metadata and publishes YMQ as today.
2. API tries to notify VPS with `job_id`, but ignores errors.
3. Worker keeps a persistent connection to VPS.
4. On signal, worker can immediately process that job id or wake its queue receive loop.
5. The YMQ message remains the durable fallback; duplicate terminal delivery is already handled as a no-op.

Expected impact: removes some queue pickup delay when the worker is between long-poll cycles. It is useful, but less important than fixing ML polling and storage chatter.

Fallback: if VPS is down, YMQ polling continues.

Risk: direct job-id execution needs idempotent claim/lock semantics if multiple workers are introduced. For one worker, existing terminal no-op behavior covers most duplicate cases.

### Option C: VPS metadata cache + pub/sub

Run Redis/Postgres/SQLite on the VPS as a low-latency mirror:

```text
cloud API / worker write durable Object Storage
cloud API / worker also write VPS cache when healthy
reads prefer VPS cache, fall back to Object Storage
VPS pub/sub drives browser realtime updates
```

Expected impact: cuts repeated job status reads/writes from Object Storage and enables push updates.

Fallback:

- write-through to Object Storage remains mandatory
- if VPS health check fails, API/worker read and write only the current S3/YMQ path
- browser falls back to cloud API polling

Risk: higher consistency complexity. Use this only after Option A and current-architecture optimizations.

### Option D: Move public API to VPS

This gives a persistent backend with connection pools and native WebSocket/SSE, but it is the highest operational change. It should still keep S3 + YMQ compatibility and a DNS or frontend fallback to the cloud API.

Expected impact: can reduce API cold-start/connection overhead and enable push, but it will not reduce ML runtime by itself.

Risk: VPS becomes part of the critical public path unless fallback is carefully implemented and tested.

## Recommended Order

1. Fix measurement labels and add explicit backend overhead fields.
2. Reduce/adapt `POLL_INTERVAL_MS`; this is now implemented as a 200 ms default.
3. Reuse ML capability cache across jobs; this is now implemented for one adapter per effective ML URL.
4. Return full job from create and remove immediate initial `getJob()`.
5. Reduce worker Object Storage writes and duplicate source metadata reads.
6. Add direct or signed final artifact URLs.
7. Add VPS realtime completion channel with browser polling fallback.
8. Add VPS wake signal if queue pickup still shows measurable delay.
9. Consider VPS metadata cache only after the simpler changes have been measured.

## Measurement Plan

Before and after each stage, record for at least 20 miss jobs:

- browser `upload_ms`
- browser `create_job_ms`
- browser `initial_get_job_ms`
- browser poll count and last poll latency
- browser `total_until_job_ms`
- browser `total_until_image_ms`
- backend `queue_wait_ms`
- backend `worker_duration_ms`
- backend `ml_total_ms`
- backend `ml_poll_overhead_ms`
- backend `worker_overhead_ms`
- stage timings for `ml_probe`, `asset_bytes_loaded`, `ml_submit`, `ml_poll`, and `artifact_store`

The current evidence suggests the first practical target is to cut worker overhead from about 1.8 s to roughly 0.6-0.9 s before adding new infrastructure.
