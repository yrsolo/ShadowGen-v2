# Current Task

## Task

Diagnose and fix queued jobs not being processed.

## Goal

Restore the production-shaped render path so newly queued jobs are claimed by the local worker, processed by the local ML service, and completed in shared state. Make the diagnostics clearer when the worker cannot reach Object Storage, YMQ, Docker, or its own control port.

## Scope Of This Stage

- verify worker container/control plane status
- verify local ML health from host and worker-side network perspective
- verify API diagnostics and the latest queued job state
- identify whether the blocker is Docker runtime, S3/Object Storage connectivity, YMQ, worker process, or ML
- restart or reconfigure local runtime if needed
- improve diagnostic messages where they are currently too vague
- record evidence and run targeted checks

## Non-Goals

- do not change ML model behavior
- do not replace YMQ/Object Storage architecture
- do not rotate or print secrets

## Risks

- stuck queued jobs may be old enough to need manual retry/requeue after worker recovery
- Docker Desktop may show stale UI state while the CLI/control pipe is unavailable
- Object Storage or YMQ endpoint connectivity failures can make the worker appear alive locally but stale in cloud diagnostics
- the current remote worker can keep serving its HTTP control UI even when its background worker/control loops are no longer processing queue messages or control actions
- the already-running remote container needs one manual restart/redeploy before the new loop-health and direct-restart behavior can protect it
