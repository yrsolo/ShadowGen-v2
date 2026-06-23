# Public API Contracts

## Main Endpoints

### `GET /health`

Health check for the API.

### `POST /v1/assets`

Upload a source asset and receive an asset reference.

### `POST /v1/jobs`

Create a render job.

The response includes the legacy summary fields (`job_id`, `status`, `cache_status`, and `reused_existing_job`) plus the full initial `job` record so clients do not need an immediate follow-up `GET /v1/jobs/{job_id}`.

### `GET /v1/jobs/{job_id}`

Get job status and metadata.

### `GET /v1/jobs/{job_id}/result`

Get the processing result, if available.

### `POST /v1/jobs/{job_id}/mark-failed`

Operator action for stale/lost job cleanup. Requires `X-Admin-Token`.

The endpoint marks a job as `failed`, records an `operator_marked_failed` trace stage, and stores the supplied reason in the job error.

### `DELETE /v1/jobs/{job_id}`

Operator action for stale/lost job cleanup. Requires `X-Admin-Token`.

The endpoint deletes job metadata and the request-cache index entry when it points at the deleted job.

### `POST /v1/jobs/cache/clear`

Operator action for cache cleanup. Requires `X-Admin-Token`.

The endpoint clears request-cache metadata and cache index entries so future submissions create fresh jobs. It does not delete job records, result artifacts, or source assets.

### `GET /v1/system/diagnostics`

Engineering-safe diagnostics for storage backend, queue/backend state, worker heartbeat, and recent jobs.

The recent job list prioritizes active `queued` and `running` jobs before completed history so stalled work is visible even when older than the latest successful renders.

Lost jobs are returned separately in `lost_jobs`. A lost job is a stale `queued` or `running` metadata record whose job id is not present in worker current/in-flight state and whose queue/worker evidence does not show matching active work.

### `GET /v1/system/runtime-config`

Read the runtime ML override visible to API and worker.

### `PUT /v1/system/runtime-config`

Update the runtime ML override. Requires `X-Admin-Token`.

### `POST /v1/system/worker-actions`

Queue a worker control command for the local worker runtime. Supported MVP actions:

- `diagnostic_probe`
- `restart_worker_process`
- `restart_container`
- `git_update_rebuild_restart`
- `clear_runtime_override`

Requires `X-Admin-Token`.

`diagnostic_probe` is the active worker/ML liveness check. The public API only queues the command; the private worker executes it and publishes the result through shared worker runtime state.

## Response Principles

- JSON for metadata responses
- binary data stays in asset storage, not inline in public job APIs
- timestamps use ISO8601 UTC
- errors use one shared shape

## Runtime Config Note

Application runtime config for API and worker is expected in `.env.shadowgen`.

## Worker Control Note

The worker also exposes a local control surface outside the cloud API:

- `GET /health` on the local worker control port
- `GET /api/status`
- `GET /api/jobs/recent`
- `GET /api/jobs/{job_id}/preview`
- `GET /api/failures/recent`
- `GET /api/actions/recent`
- `PUT /api/runtime-config` - updates `legacy_ml_base_url`, requires `X-Worker-Token`

The local worker page also exposes recent job timelines, copyable job ids, preview URLs, heartbeat age, and the last worker/ML diagnostic probe result.
It includes an editable ML URL field; saving writes the shared runtime override and refreshes the effective worker URL immediately.

## Local Development Note

Local Python commands should run from the repository virtual environment in `.venv`, not from a global interpreter.
