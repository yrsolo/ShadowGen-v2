# Current Task

## Task

Make the worker automatically distinguish the legacy ShadowGEN server from the new ShadowGen ML Service and use the matching endpoints.

## Goal

Use the new ML service handshake and sync/async render API when `/health` and `/v1/capabilities` match the current contract, while retaining strict legacy fallback through `/test` and `/v1/process`.

## Scope Of This Stage

- align ML-core capability DTOs with the new service schema
- make legacy detection require a successful `/test` response instead of accepting `404`
- support new async statuses `pending`, `completed`, and `cancelled`
- preserve explicit `v1-gan` / `v2-diff` model mapping
- update diagnostics, tests, docs, and evidence

## Risks

- malformed capability payloads must not silently route to legacy endpoints
- legacy server compatibility must remain covered
