# Migration Phases

## Phase 1

New architecture around old ML black box.

- clean API/worker/web boundaries
- local file-backed development
- worker-side legacy adapter

## Phase 2

Stable API, worker, and web flow.

- local containerized `api` and `web`
- local worker against shared remote queue and storage
- Object Storage-backed metadata and artifacts
- YMQ-backed job transport

## Phase 3

Cloud orchestration on Yandex.

- `apps/api` in Serverless Container
- `apps/web` in Serverless Container
- `apps/worker` remains local
- home ML stays private behind the worker

## Phase 4

Internal modularization and replacement of legacy ML stages.

## Phase 5

Potential next-generation GUI and interaction model.
