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
- the default idle heartbeat interval is 30 seconds so diagnostics do not flap around the current 60-second stale threshold
- worker/core integration now uses a `probe -> submit -> poll -> cancel` boundary instead of a single blocking `render()` call
- sync mode remains the compatibility fallback, while async mode is the preferred path when the ML core reports `async_enabled=true`
- worker-side concurrency is job-level only; tensor batching stays inside the ML core and Triton layer
- the local worker control page renders recent successful jobs with second-precision completion timestamps and an inline preview when the final asset can be fetched directly from the active asset store
- the default worker container is self-contained: code is baked into the image and runtime does not bind-mount the host repository or Docker socket
- `scripts/run-worker-cloud-container-detached.cmd` is the preferred always-on Docker mode for moving the worker to a separate permanent host
- container self-management is opt-in through `scripts/run-worker-cloud-container-self-managed.cmd`; in the default mode the local UI disables git update/rebuild controls
