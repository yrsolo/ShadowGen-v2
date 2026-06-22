# Plan

## Steps

1. Inspect worker loop, queue delivery adapters, and current diagnostics semantics.
2. Add visibility lease extension for in-flight queue deliveries.
3. Ignore/merge duplicate delivery of a job id already active in the local worker.
4. Change worker state so job failures do not mean the worker process is stale/dead.
5. Update web and local worker UI labels to separate worker life from last job/ML error.
6. Add focused tests for failed jobs, duplicate delivery, and visibility extension.

## Checks

- `python -m pytest tests/unit/test_worker_loop_resilience.py`
- `python -m pytest tests/integration/test_api_jobs.py tests/integration/test_system_diagnostics_failures.py`
- `python -m pytest tests/unit/test_s3_runtime_adapters.py`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
