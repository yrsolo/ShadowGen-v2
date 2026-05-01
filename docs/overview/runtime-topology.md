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
- batching decisions inside the ML core instead of the worker

## Worker Control Plane

The worker has two control surfaces:

- cloud-facing control through API-written worker actions
- local LAN-facing control UI and JSON endpoints on the worker control port

This split keeps the worker private while still allowing remote operations through the public frontend and API.

## Worker Container Modes

The normal worker container mode is self-contained:

- worker code and package code are copied into the image
- the host repository is not mounted
- Docker socket is not mounted
- process restart remains available
- git update/rebuild/recreate actions are disabled

There is a separate opt-in self-managed mode for local operator experiments. That mode mounts the repository plus Docker socket and enables the worker to rebuild/recreate itself. It is intentionally not the default because large Windows or network-folder bind mounts can destabilize Docker Desktop and because Docker socket access gives the container host-level control.
