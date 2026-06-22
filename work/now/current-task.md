# Current Task

## Task

Fix worker diagnostics and queue behavior when async ML processing outlives the queue visibility timeout.

## Goal

Prevent a running async job from being claimed repeatedly, and make the UI distinguish worker liveness from the last job or ML failure.

## Scope Of This Stage

- inspect worker loop delivery handling and state updates
- keep YMQ messages invisible while a worker is still processing them
- avoid starting a duplicate executor for the same in-flight job id
- keep worker heartbeat/life independent from last job failure
- update worker and web diagnostics labels
- add focused tests and evidence

## Risks

- ack/nack behavior must remain correct for real processing failures
- long async ML jobs must not be lost or duplicated
- UI must still expose last job/ML errors without marking a healthy worker as dead
