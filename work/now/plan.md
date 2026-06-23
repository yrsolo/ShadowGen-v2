# Plan

## Steps

1. Inspect current capability refresh defaults and web upload preparation.
2. Increase warm ML capability cache duration for local ML operation.
3. Convert large PNG uploads without alpha to JPEG while preserving transparent PNGs as PNG.
4. Update runtime/web documentation and latency analysis.
5. Run focused worker/ML adapter checks, web build, and docs checks.
6. Record implementation evidence in `work/now/evidence.md`.

## Checks

- `python -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/smoke/test_worker_process_job.py -q`
- `python -m pytest tests/unit/test_worker_runtime_composition.py tests/unit/test_worker_loop_resilience.py -q`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
