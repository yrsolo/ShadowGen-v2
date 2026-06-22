# Runtime Topology

## Current Shape

```text
browser
  -> web
  -> api
  -> queue + shared state
  -> worker
  -> ML-core adapter boundary
  -> ML service
```

## Shared State

Shared state is currently backed by Object Storage in the cloud-shaped runtime.

Stored there:

- source assets
- final artifacts
- debug artifacts
- job metadata
- runtime config
- worker runtime state
- worker actions

## Queue

Job transport uses Yandex Message Queue in the cloud-shaped runtime.

The queue carries business jobs only.

- the worker owns business-job concurrency
- the worker may keep several jobs in flight
- queue deliveries are acknowledged only after worker handling completes
- active queue deliveries have their visibility extended while async ML processing is still running
- a redelivered message for a job already active in the same worker is treated as a duplicate delivery, not as a second job start
- the worker does not build tensor batches
- batching remains internal to the ML core and Triton path when supported

## Worker / ML Core Boundary

The worker now talks to the ML layer through a dedicated pipeline boundary:

- `probe(force_refresh=False)`
- `submit(context)`
- `poll(submission)`
- `cancel(submission)`

The worker chooses execution mode from ML-core capabilities:

- `async` when the ML core reports `async_enabled=true`
- `sync` as the normal compatibility fallback
- `legacy-sync` when only the old ShadowGEN transport is available

This keeps:

- product API contracts stable
- ML-core transport details out of application code
- ML-core transport details out of the public API process
- batching decisions inside the ML core instead of the worker

## Worker Control Plane

The worker has two control surfaces:

- cloud-facing control through API-written worker actions
- local LAN-facing control UI and JSON endpoints on the worker control port

This split keeps the worker private while still allowing remote operations through the public frontend and API.

Worker heartbeat in diagnostics means the worker process is still updating shared runtime state. It is separate from ML health and from the result of the last job; ML probe, submit, poll, and job trace fields carry those failures.

## Worker Container Mode

The worker container mode is self-contained:

- worker code and package code are copied into the image
- the host repository is not mounted
- Docker socket is not mounted
- the container runs detached with `--restart unless-stopped`
- process restart remains available
- git update/rebuild/recreate actions are disabled
