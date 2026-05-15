# Current Task

## Task

Implement the architecture remediation plan from the repository audit.

## Goal

Improve architecture quality and operational safety by:

1. protecting mutating system/control-plane API endpoints with an admin token
2. changing queue consumption from delete-before-process to explicit delivery acknowledgement
3. moving job lifecycle state transitions into the domain layer
4. making duplicate or redelivered terminal jobs idempotent in the worker path
5. removing API-side ML-core probing so only the worker talks to ML
6. reducing diagnostics payload risk by moving worker recent-job previews behind a separate endpoint
7. strengthening architecture and CI guardrails
8. updating documentation and evidence for the new rules

## Scope Of This Stage

- add API admin-token config and enforce it on `PUT /v1/system/runtime-config` and `POST /v1/system/worker-actions`
- let the web engineering client optionally send the admin token from `NEXT_PUBLIC_ADMIN_API_TOKEN`
- introduce a queue delivery envelope with `ack`, `nack`, and optional visibility extension
- update memory, file, and YMQ queues plus worker loop tests for ack-after-success behavior
- add domain `JobEntity` lifecycle methods and use them from process-job orchestration
- make process-job execution skip already terminal jobs safely
- build API diagnostics only from queue, storage, runtime config, and worker-published state
- remove base64 previews from worker status JSON and expose preview bytes through a dedicated local endpoint
- expand architecture boundary tests and CI checks

## Risks

- breaking existing tests that assume direct `consume()` queue behavior
- accidentally requiring admin auth for read-only diagnostics
- making local engineering panel unusable without clear token configuration
- changing worker queue semantics without preserving file/memory local behavior
- overcorrecting DTO boundaries beyond what can be safely completed in one pass
