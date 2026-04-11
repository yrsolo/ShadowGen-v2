# Architecture Decisions

## ADR-001

Use one repository for web, api, worker, and shared packages.

## ADR-002

Do not integrate the old ML core directly into application or domain layers; isolate it behind a legacy adapter.

## ADR-003

Split API and worker from the first stage.

## ADR-004

Keep contracts in a dedicated shared package.

## ADR-005

Allow in-memory infrastructure during bootstrap to avoid premature platform coupling.

## ADR-006

Do not shape v2 public contracts around legacy request and response compatibility; keep compatibility concerns isolated inside the legacy adapter.

## ADR-007

Keep local development shaped like separate services. Shared in-memory state is allowed for tests, but file-backed local adapters are the default for multi-process development.
