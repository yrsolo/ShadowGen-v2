# ShadowGen v2

ShadowGen v2 is a cloud-shaped image processing system for product-style shadow generation.

Current user flow:

1. upload an image in the web UI
2. create a render job through the API
3. let the worker consume the job from the queue
4. call ML through the worker-side pipeline adapter
5. store final and debug artifacts in shared storage
6. fetch result previews and diagnostics back through the API

Current behavior highlights:

- duplicate render submissions with the same image bytes and the same render settings are short-circuited before queue publish and reuse the existing live or completed job
- engineering diagnostics and the worker control UI show recent jobs with timestamps, lightweight previews, cache/reuse status, and expandable processing timelines
- the worker can run an explicit diagnostic probe that checks worker round-trip health and worker-side ML availability without exposing the private worker host

## Current Runtime Shape

```text
web -> api -> queue + shared state -> worker -> pipeline adapter -> ML service
```

Current deployment split:

- `apps/web` runs in Yandex Serverless Containers
- `apps/api` runs in Yandex Serverless Containers
- queue uses Yandex Message Queue
- shared state and artifacts use Yandex Object Storage
- `apps/worker` stays on the local GPU machine
- the ML service stays behind the local worker
- the worker supports both sync compatibility mode and async-native ML-core orchestration

## Active Repositories And Modules

Top-level runtime modules:

- `apps/api` - FastAPI transport and composition layer
- `apps/web` - Next.js UI for user flow and engineering diagnostics
- `apps/worker` - job execution loop and local worker control plane
- `apps/worker` - job execution loop, ML-core orchestration, and local worker control plane
- `packages/contracts` - shared DTOs and public/internal contracts
- `packages/application` - use cases and ports
- `packages/domain` - entities, statuses, exceptions, value objects
- `packages/pipeline` - pipeline context, interfaces, and output model
- `packages/pipeline` - worker-facing ML-core submission, polling, and output model
- `packages/adapters` - storage, queue, runtime stores, and legacy/new ML adapters
- `packages/schema` - placeholder area for future standalone schema artifacts

## What Is Source Of Truth

For architecture and behavior, prefer:

- runtime entrypoints in `apps/*/src`
- `packages/*` code
- tests
- scripts used to run or deploy the system

Do not treat older bootstrap leftovers in app-local folders as authoritative runtime structure.

## Quick Start

Application runtime config lives in `.env.shadowgen`.

### Local cloud-shaped run

1. copy `.env.shadowgen.example` to `.env.shadowgen`
2. fill storage, queue, and ML settings
3. start local `api` and `web`
4. start the worker either on the host or in a local container

Commands:

- `scripts\run-local-containers.cmd`
- `scripts\run-worker-cloud.cmd`
- `scripts\run-worker-cloud-container.cmd`

The worker container script builds a self-contained image and starts `shadowgen-worker` detached with Docker `--restart unless-stopped`. It does not mount the repository or Docker socket, so in-UI git update/rebuild controls stay disabled by design.

Worker control endpoints:

- UI: `http://localhost:8081`
- JSON status: `http://localhost:8081/api/status`
- runtime ML URL update: `PUT http://localhost:8081/api/runtime-config` with `X-Worker-Token`

## Public URLs

- web: `https://shadowgen.solofarm.ru`
- api health: `https://api.shadowgen.solofarm.ru/health`

## Main API Surface

- `GET /health`
- `POST /v1/assets`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `GET /v1/system/diagnostics`
- `GET /v1/system/runtime-config`
- `PUT /v1/system/runtime-config` - requires `X-Admin-Token`
- `POST /v1/system/worker-actions` - requires `X-Admin-Token`

## Documentation

Start here:

- [Documentation Index](docs/README.md)
- [Quick Start](docs/overview/quick-start.md)
- [Permanent Worker Host](docs/overview/permanent-worker-host.md)
- [Runtime Topology](docs/overview/runtime-topology.md)
- [Repository Map](docs/overview/repository-map.md)

Detailed module reference:

- [Apps And Packages Reference](docs/reference/modules/README.md)
- [Runtime And Scripts](docs/reference/runtime-and-scripts.md)

Contracts:

- [API Contract](docs/contracts/api.md)
- [Jobs Contract](docs/contracts/jobs.md)
- [ML Black Box Contract](docs/contracts/ml-black-box.md)
- [New ML Service Contract](docs/contracts/new-ml-service.md)
