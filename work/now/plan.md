# Plan

## Steps

1. Trace the worker path that writes runtime state into S3/Object Storage during idle polling
2. Refactor worker state publishing so idle polls use reads and write state only on changes or a throttled heartbeat
3. Add focused tests for idle heartbeat throttling and runtime-config refresh behavior
4. Update tracking and any touched worker reference docs
5. Run targeted verification and record evidence

## Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_loop_resilience.py tests/unit/test_worker_state_service.py tests/unit/test_s3_runtime_adapters.py -q`
