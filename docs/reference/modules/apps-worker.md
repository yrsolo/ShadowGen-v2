# Worker App

Path:

- `apps/worker/src/shadowgen_worker`

Entry point:

- `apps/worker/src/shadowgen_worker/main.py`

Responsibilities:

- consume jobs
- execute the render pipeline
- update job state and artifacts
- maintain worker runtime state with event-driven updates and a throttled idle heartbeat
- expose a local worker control UI and JSON endpoints
- execute worker control actions

Main files:

- `main.py` - runtime composition
- `loop.py` - job consumption loop
- `executor.py` - job execution wrapper
- `state.py` - worker runtime state management
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
