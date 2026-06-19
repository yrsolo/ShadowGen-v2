# Plan

## Steps

1. Add a local worker runtime-config update endpoint protected by `X-Worker-Token`.
2. Update worker state after the shared runtime override changes.
3. Add editable ML URL controls to the local worker HTML dashboard.
4. Add endpoint/UI contract tests.
5. Update worker docs and evidence.

## Checks

- `python -m pytest tests/unit/test_worker_control_app.py tests/unit/test_worker_state_service.py`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
