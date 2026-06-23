# Current Task

## Task

Complete the first production integration of the VPS realtime accelerator.

## Goal

Put the realtime service behind a production HTTPS domain, connect API queued notifications, connect browser SSE fallback, connect worker lifecycle event publishing, and preserve the old YMQ/Object Storage path as fallback.

## Scope Of This Stage

- configure DNS/TLS for `https://rt.shadowgen.solofarm.ru`
- keep `apps/realtime` deployed as `shadowgen-realtime` under `/opt/shadowgen-realtime`
- add shared realtime signing and HTTP accelerator adapter
- wire API best-effort queued notifications and job-scoped subscription metadata
- wire Web SSE observation with API polling fallback
- wire worker best-effort lifecycle event publishing
- deploy updated realtime/API/Web/worker pieces
- document runtime settings and verification evidence

## Non-Goals

- do not implement worker wake hints in this stage
- do not move any durable state from Object Storage/YMQ to the VPS
- do not expose worker control endpoints through the realtime service
- do not print or commit generated realtime/API/worker tokens

## Risks

- generated VPS secrets must remain only in server-local `.env.realtime`
- local `.env.shadowgen` may contain copied deployment secrets but remains gitignored
- public SSE must not reveal job results or asset bytes
- internal endpoints must fail closed when tokens are missing or wrong
- API and worker must treat realtime failures as best-effort
- worker wake hints remain future work, so pickup latency is still bounded by YMQ polling behavior
