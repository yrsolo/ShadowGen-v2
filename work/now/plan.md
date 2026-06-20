# Plan

## Steps

1. Probe `http://192.168.1.8:9001` for `/health`, `/v1/capabilities`, and legacy fallback signals when reachable.
2. Inspect worker processing trace around ML probe, submit, poll, result mapping, and artifact storage.
3. Preserve compact ML failure context in job trace and worker diagnostics without logging image payloads.
4. Add tests that failed ML submit/poll responses leave actionable trace messages.
5. Update docs/evidence with the diagnostic path and checks.

## Checks

- `python -m pytest tests/unit/test_ml_core_adapter.py tests/unit/test_process_job_failures.py`
- `python -m pytest tests/unit/test_worker_state_service.py tests/unit/test_worker_control_app.py`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
