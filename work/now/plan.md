# Plan

## Steps

1. Add an admin-token dependency for mutating system endpoints while keeping read-only diagnostics public.
2. Update the web engineering client to send the configured admin token when operator actions are used.
3. Replace queue `consume()` with explicit `receive()` delivery envelopes and keep compatibility where needed for tests.
4. Ack queue messages only after worker execution completes; nack or leave visible again on failure.
5. Add domain job lifecycle methods and route process-job state changes through them.
6. Treat duplicate deliveries for already terminal jobs as successful no-ops.
7. Remove API-side ML-core adapter construction and use worker-published capability state for diagnostics.
8. Move worker recent-job previews out of `/api/status` and into a dedicated local preview endpoint.
9. Expand architecture boundary tests and CI checks for Python, web build, and stricter import rules.
10. Update docs and evidence after implementation and verification.

## Checks

- `python -m pytest tests/unit/test_architecture_boundaries.py`
- `python -m pytest tests/unit/test_worker_loop_resilience.py tests/integration/test_ymq_adapter.py`
- `python -m pytest tests/unit/test_process_job_failures.py tests/smoke/test_worker_process_job.py`
- `python -m pytest tests/integration/test_runtime_config_api.py tests/integration/test_worker_action_api.py tests/integration/test_api_jobs.py`
- `python -m pytest`
- `cmd /c npm run build` in `apps/web`
