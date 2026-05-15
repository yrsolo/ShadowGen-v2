# Architecture Overview

ShadowGen v2 is organized as a clean-architecture, hexagonal system with explicit boundaries between transport, application logic, domain logic, pipeline integration, and infrastructure adapters.

## Runtime Topology

```text
web -> api -> queue + shared state -> worker -> render pipeline -> ML adapter -> ML service
```

## Current Deployment Shape

- `apps/web` runs in Yandex Serverless Containers
- `apps/api` runs in Yandex Serverless Containers
- queue uses Yandex Message Queue
- source assets, final artifacts, debug artifacts, job metadata, runtime config, worker state, and worker actions use Object Storage-backed shared state
- `apps/worker` runs on the local GPU machine
- the ML service is reached only through the worker-side pipeline adapter

## Boundary Rules

- `apps/api` is transport and composition only
- `apps/worker` is execution and worker-side composition only
- `apps/web` talks only to the API
- `packages/application` depends on ports and contracts, not infrastructure
- `packages/domain` contains entities, invariants, statuses, and exceptions only
- `packages/domain` does not depend on public API contract DTOs
- `packages/pipeline` defines the processing interface and pipeline payloads
- `packages/adapters` implements storage, queue, runtime stores, and ML bridges
- legacy ML details are allowed only under `packages/adapters/**/legacy_*`

## Main Runtime Responsibilities

### Web

- upload source images
- configure render parameters
- submit jobs
- poll job state
- render result previews
- expose engineering diagnostics and worker action controls

### API

- validate and accept uploads
- create jobs
- expose job state and result metadata
- expose diagnostics from queue, storage, and worker-published state
- protect runtime config updates and worker control actions behind admin-token auth

### Worker

- consume jobs from the queue
- acknowledge queue deliveries only after handling completes
- load source assets from shared state
- call the render pipeline
- store final and debug artifacts
- update job state
- expose local worker diagnostics and action controls on a local control port

### Pipeline

- accept image bytes plus a render request
- return pipeline artifacts, metrics, and warnings
- isolate the rest of the system from ML transport details

## Current Variants

State backends:

- `memory` for tests
- `file` for older local single-machine flows
- `s3` for the current cloud-shaped runtime

Queue backends:

- `memory` for tests
- `file` for older local development
- `ymq` for the cloud-shaped runtime
