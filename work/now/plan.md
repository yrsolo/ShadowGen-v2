# Plan

## Steps

1. Inspect current worker ML polling configuration, docs, and tests.
2. Lower the default worker async ML polling interval for local ML.
3. Update env examples and worker/runtime documentation to describe the faster polling default.
4. Run focused worker/process-job tests and docs checks.
5. Revisit the no-VPS optimization list and update the working latency analysis if needed.
6. Record implementation evidence in `work/now/evidence.md`.

## Checks

- `python -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/smoke/test_worker_process_job.py -q`
- `python -m pytest tests/unit/test_worker_loop_resilience.py -q`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
