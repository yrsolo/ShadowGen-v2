# Current Task

## Task

Reduce remaining no-VPS overhead after ML polling improvements.

## Goal

Cut avoidable backend and client/API latency in the current local-ML setup while keeping behavior compatible with the existing serverless/YMQ/Object Storage fallback.

## Scope Of This Stage

- reduce repeated worker-side ML capability probes on warm jobs
- reduce upload/source payload size for large non-transparent images
- keep alpha-preserving behavior for transparent PNGs
- run focused worker, web, and contract checks
- record checks and results in `work/now/evidence.md`

## Risks

- longer capability cache means capability changes are detected less frequently unless the ML URL changes or an explicit diagnostic probe is used
- client-side JPEG conversion must not flatten transparent PNG uploads
- smaller upload payloads change source bytes and therefore cache keys for newly uploaded images
