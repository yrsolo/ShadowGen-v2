# Current Task

## Task

Reduce async ML polling latency and identify the next no-VPS optimizations.

## Goal

Cut the largest avoidable `ml_poll` delay in the current local-ML setup, keep behavior compatible with the existing serverless/YMQ/Object Storage fallback, and leave clear evidence for the next optimization stage.

## Scope Of This Stage

- reduce worker-side async ML polling interval from the current one-second cadence
- update runtime examples/docs that expose the polling interval
- run focused tests around worker/process-job behavior
- re-check low-risk no-VPS optimization candidates after the polling change
- record checks and results in `work/now/evidence.md`

## Risks

- shorter ML polling increases worker-to-ML status requests
- tests using stub async polling may need explicit intervals to stay fast
- polling changes must not affect sync or legacy-sync execution paths
