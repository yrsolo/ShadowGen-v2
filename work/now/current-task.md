# Current Task

## Task

Reduce async ML polling latency and buffer worker job metadata writes.

## Goal

Cut avoidable worker-side latency in the current local-ML setup, especially polling and Object Storage metadata write overhead, while keeping behavior compatible with the existing serverless/YMQ/Object Storage fallback.

## Scope Of This Stage

- reduce worker-side async ML polling interval from the current one-second cadence
- update runtime examples/docs that expose the polling interval
- buffer worker job metadata writes so fast trace stages are persisted at checkpoints instead of every start/finish
- run focused tests around worker/process-job behavior
- re-check low-risk no-VPS optimization candidates after the polling change
- record checks and results in `work/now/evidence.md`

## Risks

- shorter ML polling increases worker-to-ML status requests
- tests using stub async polling may need explicit intervals to stay fast
- polling changes must not affect sync or legacy-sync execution paths
- fewer intermediate job writes means Engineering diagnostics may see less per-stage progress during sub-second phases, while worker runtime state still shows live in-flight jobs
