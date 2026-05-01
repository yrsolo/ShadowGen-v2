# Plan

## Steps

1. Extend worker `Recent Jobs` payload entries with formatted completion time and optional preview source from the active asset store
2. Update the worker dashboard HTML so recent jobs show timestamp, preview, and duration compactly
3. Normalize request-cache inputs so identical image bytes and identical render params reuse the same job regardless of asset ID
4. Teach job repositories and create-job orchestration to reuse existing live or completed jobs before queue publish
5. Update docs, tracking, and focused tests
6. Rebuild and redeploy the updated containers so the worker UI and cloud runtime match the repository state
7. Remove cache-hit latency by switching from full asset reads and full job scans to metadata-driven hashes plus direct request-cache indexes
8. Change the default worker-container launch to use the code baked into the image with no repository or Docker-socket bind mounts
9. Keep the self-managed git-update flow available only through a separate opt-in script/documented mode
10. Remove S3/Object Storage full job scans from request-cache miss handling so `POST /v1/jobs` does not slow down as job history grows
11. Add `shadow.model` to shared render and ML-core contracts, including the updated `source.image_base64` field name
12. Update the web UI with a phone-first basic flow, model selector, and advanced mode for the previous manual controls/details
13. Update focused tests and documentation for the model-selection behavior
14. Align the minimal mobile composition with `design/ref`, including top `Top/Side`, bottom `Min/Max/Engineering`, preview-embedded upload/camera entry, and preview reset control
15. Add a permanent-worker-host runbook and self-documenting `.env.shadowgen` template comments
16. Add a detached Docker worker launch script for an always-on host

## Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_control_app.py tests/unit/test_create_job.py tests/integration/test_api_jobs.py tests/integration/test_local_file_runtime.py -q`
- rebuild worker image and redeploy `api`/`web` serverless revisions
- verify request-cache fast path with focused storage and API tests
- build the worker image and verify the default run script no longer contains repository or Docker socket mounts
- deploy the API container after the S3 request-cache hot-path change
- run ML-core mapper/unit tests and web build after the model-selection UI/contract update
- run docs check after adding the worker host deployment guide
- inspect the detached worker script for expected restart policy and absence of repository/Docker-socket mounts
