# Plan

## Steps

1. Inspect current worker metadata write points and trace expectations.
2. Remove fast-stage `job_repository.update()` calls that do not need to be externally visible immediately.
3. Keep checkpoints for `running`, submitted/async waiting, terminal success, terminal failure, missing asset, and terminal no-op.
4. Add focused coverage for reduced process-job repository write count.
5. Update worker docs and latency analysis.
6. Run focused worker/process-job, API, S3, web, and docs checks.
7. Record implementation evidence in `work/now/evidence.md`.

## Checks

- `python -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/smoke/test_worker_process_job.py -q`
- `python -m pytest tests/unit/test_process_job_write_buffering.py -q`
- `python -m pytest tests/unit/test_worker_loop_resilience.py -q`
- `python -m pytest tests/integration/test_api_jobs.py tests/unit/test_s3_runtime_adapters.py -q`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
