# Current Task

## Task

Reduce unnecessary worker `PUT` traffic to S3/Object Storage during idle polling, so the worker does not rewrite runtime state on every empty queue poll.

## Goal

Change worker runtime-state behavior so that:

1. idle polling can continue to use reads where needed
2. `PUT` to `runtime/worker-state.json` happens on meaningful state changes or a rare heartbeat, not every second
3. worker diagnostics and control UI still show a useful heartbeat age and effective runtime config
4. the change is covered by focused tests

## Scope Of This Stage

- inspect worker loop and runtime state publishing path
- refactor worker state persistence to reduce idle write amplification
- preserve clean architecture boundaries
- update tracking and evidence
- run targeted verification

## Risks

- making worker heartbeat too sparse and causing false stale/offline diagnostics
- missing runtime-config override changes while the worker is idle
- introducing race conditions between job loop and control-action loop state updates
