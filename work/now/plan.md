# Plan

## Steps

1. Add compact job trace contracts and cache-hit markers.
2. Record create-job cache lookup, queue, worker processing, ML, artifact, completion, and failure stages.
3. Add worker `diagnostic_probe` action and publish worker/ML probe results in runtime state.
4. Update system diagnostics to use a five-minute stale threshold.
5. Redesign engineering and worker task lists around time, preview, copyable job id, and expandable timeline.
6. Add focused tests for trace, cache reuse, stale threshold, and diagnostic probe.
7. Update docs and evidence after implementation and verification.

## Checks

- `python -m pytest tests/unit/test_create_job.py tests/unit/test_process_job_failures.py tests/smoke/test_worker_process_job.py`
- `python -m pytest tests/unit/test_worker_state_service.py tests/unit/test_worker_control_app.py tests/integration/test_worker_action_api.py`
- `python -m pytest tests/integration/test_api_jobs.py tests/integration/test_system_diagnostics_failures.py`
- `python -m pytest`
- `cmd /c npm run build` in `apps/web`
