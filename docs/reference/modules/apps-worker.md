# Worker App

Path:

- `apps/worker/src/shadowgen_worker`

Entry point:

- `apps/worker/src/shadowgen_worker/main.py`

Responsibilities:

- consume jobs
- execute the render pipeline
- probe ML-core capabilities and select sync vs async worker/core mode
- keep bounded business jobs in flight toward the ML core
- update job state and artifacts
- maintain worker runtime state with event-driven updates and a throttled idle heartbeat
- publish active worker and ML diagnostic probe results
- expose a local worker control UI and JSON endpoints
- execute worker control actions

Main files:

- `main.py` - runtime composition
- `loop.py` - bounded in-flight job orchestration loop
- `executor.py` - job execution wrapper
- `state.py` - worker runtime state management, capability snapshots, and in-flight tracking
- `control_app.py` - local FastAPI control surface
- `control_loop.py` - worker action polling loop
- `control_actions.py` - action execution
- `metadata.py` - version metadata
- `self_manage_helper.py` - container self-management helper

Not responsible for:

- public browser-facing UI
- public API transport

Runtime note:

- when `STATE_BACKEND=s3`, the worker still polls queue/config as needed, but `runtime/worker-state.json` is rewritten only on meaningful state changes or on the throttled idle heartbeat interval
- job trace metadata is buffered through fast worker stages and persisted at checkpoints such as running start, async wait, terminal success, and terminal failure
- the default idle heartbeat interval is 30 seconds; diagnostics mark worker state stale only after five minutes without a fresh heartbeat/probe
- worker/core integration now uses a `probe -> submit -> poll -> cancel` boundary instead of a single blocking `render()` call
- queue messages are acknowledged only after worker handling completes; failed handling is nacked so the queue can redeliver
- the worker extends queue visibility for active deliveries, so long async ML polling does not redeliver the same business job before processing finishes
- duplicate delivery of a job id already active in the same worker updates the active receipt handle instead of starting a second executor
- sync mode remains the compatibility fallback, while async mode is the preferred path when the ML core reports `async_enabled=true`
- worker-side concurrency is job-level only; tensor batching stays inside the ML core and Triton layer
- a runtime ML override in shared runtime config has priority over `LEGACY_ML_BASE_URL`; clear it before relying on a changed worker env value
- the local worker control page renders recent jobs with timestamps, preview URLs, copyable job ids, and expandable stage timelines; image bytes are served only by `GET /api/jobs/{job_id}/preview`
- the local worker control page can update the shared runtime ML URL through token-protected `PUT /api/runtime-config`; the effective URL is republished to worker state immediately and applies to subsequent jobs
- `diagnostic_probe` checks the worker action round-trip and probes the effective ML URL from the worker side, using the ML-core health path or legacy `/test` compatibility path
- service detection is contract-based: a valid ML-core handshake selects sync/async `/v1/render*`; legacy mode requires a 2xx `/test` and uses `/v1/process`
- the worker reuses one ML-core adapter per effective ML URL, so capability probing is cached across warm jobs until `CAPABILITIES_REFRESH_INTERVAL_SEC` expires or the effective ML URL changes
- new ML-service async statuses `pending`, `running`, `completed`, `failed`, and `cancelled` are mapped into the business job lifecycle
- ML HTTP failures are recorded with method, endpoint path, HTTP status, ML error code, and message in the failing job trace stage
- async ML terminal errors are recorded on the `ml_poll` trace stage with ML job id, request id, status, error code, and details when provided
- worker runtime state separates last submit and poll errors so diagnostics can show whether the failure happened while submitting to ML or while waiting for async completion
- worker heartbeat/life means the worker process is updating state; the last job or ML error is shown separately and does not by itself mean the worker is dead
- the worker container is self-contained: code is baked into the image and runtime does not bind-mount the host repository or Docker socket
- `scripts/run-worker-cloud-container.cmd` starts the always-on Docker worker detached with `--restart unless-stopped`
- container self-management is intentionally disabled in the supported container script, so the local UI disables git update/rebuild controls
