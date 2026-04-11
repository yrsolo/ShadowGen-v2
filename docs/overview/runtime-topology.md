# Runtime Topology

## Current Shape

```text
browser
  -> web
  -> api
  -> queue + shared state
  -> worker
  -> pipeline adapter
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

## Worker Control Plane

The worker has two control surfaces:

- cloud-facing control through API-written worker actions
- local LAN-facing control UI and JSON endpoints on the worker control port

This split keeps the worker private while still allowing remote operations through the public frontend and API.
