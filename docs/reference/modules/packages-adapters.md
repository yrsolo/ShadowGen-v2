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
  - file, memory, and YMQ job queues
- `runtime/`
  - runtime config, worker state, worker action stores, and adapter factory wiring
- `legacy_pipeline/`
  - old ML bridge, mapper, HTTP adapter, stub adapter

Key file:

- `runtime/factories.py` - central runtime wiring for storage, queue, runtime config, worker state, and worker actions

Design rule:

- adapter code may know transport and infrastructure details
- only `legacy_pipeline/` may know the old ML service contract
