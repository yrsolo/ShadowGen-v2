# Plan

## Steps

1. Done - checked Docker, worker control port, ML health, API health, diagnostics, and latest stuck job.
2. Done - identified the current blocker as a stale/dead remote worker background loop while its HTTP control plane still answers.
3. Pending manual remote action - restart/redeploy the worker container on `192.168.1.6` so the fixed worker code can run there.
4. Done - improved diagnostics so future failures distinguish heartbeat freshness, worker control probe, ML probe, current job, and last errors.
5. Done - targeted tests/build/docs checks passed and evidence was recorded.

## Checks

- local worker control `/api/status`
- local ML `/health`
- public API `/health`
- public diagnostics endpoint
- targeted Python tests for diagnostics/runtime changes
- `git diff --check`

## Current Runtime Follow-Up

- Manually restart or redeploy the worker container on `192.168.1.6`.
- After restart, check `http://192.168.1.6:8081/health`; the fixed version should include `process.threads.worker_loop` and `process.threads.control_loop`.
- Re-check the queued job list; the worker should claim the pending YMQ message instead of staying idle.

## Deliverables

- recovered worker/runtime if possible
- diagnostics improvements if code changes are needed
- updated `work/now/evidence.md`
