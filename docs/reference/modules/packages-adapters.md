# Adapters Package

Path:

- `packages/adapters/src/shadowgen_adapters`

Purpose:

- implement ports for storage, queue, shared runtime state, and ML integration

Submodules:

- `storage/`
  - file, memory, and S3 asset stores
- `jobs/`
  - file, memory, and S3 job repositories
- `queue/`
  - file, memory, and YMQ job queues with explicit delivery acknowledgement
- `runtime/`
  - runtime config, worker state, worker action stores, and adapter factory wiring
- `ml_core/`
  - new ML-core handshake detection, sync/async adapter, current status mapping, stage metrics, transport errors, and stub behavior
- `legacy_pipeline/`
  - old ShadowGEN sync compatibility bridge, mapper, HTTP adapter, and stub adapter

Key file:

- `runtime/factories.py` - central runtime wiring for storage, queue, runtime config, worker state, and worker actions

Design rule:

- adapter code may know transport and infrastructure details
- `ml_core/` may know the new worker-to-core HTTP contract
- only `legacy_pipeline/` may know the old ML service contract

Runtime note:

- the S3 and file job repositories now keep a request-cache index for fast duplicate-request reuse
- the asset stores persist a source hash in metadata so request-cache lookup can avoid downloading the full source image on a cache hit
- S3 job repository cache lookup does not fall back to listing every job on a miss; this keeps `POST /v1/jobs` stable as job history grows
- queue adapters expose `receive()` delivery envelopes; YMQ messages are deleted only when the worker calls `ack()`
- ML service detection never treats `/test` 404 as legacy readiness; legacy mode requires a 2xx `/test`, while a successful ML-core handshake always uses `/v1/render*`
