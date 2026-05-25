# Public API Contracts

## Main Endpoints

### `GET /health`

Health check for the API.

### `POST /v1/assets`

Upload a source asset and receive an asset reference.

### `POST /v1/jobs`

Create a render job.

### `GET /v1/jobs/{job_id}`

Get job status and metadata.

### `GET /v1/jobs/{job_id}/result`

Get the processing result, if available.

### `GET /v1/system/diagnostics`

Engineering-safe diagnostics for storage backend, queue/backend state, worker heartbeat, and recent jobs.

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

The local worker page also exposes recent job timelines, copyable job ids, preview URLs, heartbeat age, and the last worker/ML diagnostic probe result.

## Local Development Note

Local Python commands should run from the repository virtual environment in `.venv`, not from a global interpreter.
