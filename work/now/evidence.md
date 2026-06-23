# Evidence

## 2026-06-23 Warm Probe And Upload Payload Reduction

- live screenshots after polling changes showed `duration_ms=936`, `ml_total_ms=241`, `ml_probe=122`, `asset_bytes_loaded=113`, `ml_submit=52`, `ml_poll=360`, and `artifact_store=123`; this made non-poll overhead the next target
- raised the default `CAPABILITIES_REFRESH_INTERVAL_SEC` from 45 seconds to 300 seconds in worker config, ML-core adapter default, and env examples
- warm jobs against the same effective ML URL should now avoid the remote `/health` + `/v1/capabilities` handshake for longer; changing the effective ML URL still creates a fresh adapter
- web upload preparation now repacks large opaque PNG files (`>=300000` bytes) as JPEG after checking every alpha byte on the canvas
- transparent PNG files keep the alpha-preserving PNG path, and oversized transparent PNG files still resize as PNG
- updated worker/runtime/web docs and `work/now/latency-analysis.md`
- `python -m pytest tests/unit/test_ml_core_adapter.py tests/unit/test_worker_runtime_composition.py tests/unit/test_worker_loop_resilience.py tests/unit/test_process_job_failures.py tests/smoke/test_worker_process_job.py -q` -> `15 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed
- `git diff --check` -> passed with CRLF warnings only

## 2026-06-23 Worker Job Write Buffering

- buffered fast `ProcessJobUseCase` trace writes by removing intermediate `job_repository.update()` calls around `ml_probe`, `asset_bytes_loaded`, `ml_submit` start, and `artifact_store` start
- kept persisted checkpoints for worker claim, running start, async wait, sync submit-before-complete, terminal success, terminal failure, missing asset failure, and terminal no-op
- fast async success path now persists job metadata 4 times: claim, running start, async wait, and terminal success
- final persisted job trace still contains `worker_claimed`, `asset_ref_loaded`, `ml_probe`, `asset_bytes_loaded`, `ml_submit`, `ml_poll`, `artifact_store`, and `completed`
- added `tests/unit/test_process_job_write_buffering.py`
- `python -m pytest tests/unit/test_process_job_write_buffering.py -q` -> `1 passed`
- `python -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/smoke/test_worker_process_job.py tests/unit/test_worker_runtime_composition.py tests/unit/test_worker_loop_resilience.py tests/integration/test_api_jobs.py tests/unit/test_s3_runtime_adapters.py -q` -> `22 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed

## 2026-06-23 Create Response And S3 Metadata Latency Reduction

- live diagnostics for job `66c8b721-c004-4590-be67-0ddaceb28510` showed `duration_ms=2540`, `ml_total_ms=236`, `ml_poll_ms=1317`, `ml_probe_ms=173`, `asset_bytes_ms=222`, and `artifact_store_ms=218`
- the same job had `created_at=11:35:03.555597Z`, `started_at=11:35:04.406925Z`, and `finished_at=11:35:06.947085Z`, so queue/API/pre-start time was about 851 ms and worker time was about 2540 ms
- `ml_poll_ms - ml_total_ms` was still about 1081 ms, which matches an old one-second worker polling cadence; the repository code is already at `POLL_INTERVAL_MS=200`, so the live worker likely still needs rebuild/restart or is running an older image/process
- `CreateJobResponse` now includes the full initial `job` record while keeping legacy summary fields
- the web client uses `createResponse.job` to avoid the immediate follow-up `GET /v1/jobs/{job_id}` when the API supports the new response
- the web client still falls back to the old `GET /v1/jobs/{job_id}` path when talking to an older API revision
- `S3AssetStore` now caches asset metadata in the adapter instance, avoiding a repeated `assets/meta/*.json` read for `get_ref()` followed by `get_bytes()` or `get_bytes()` followed by `get_source_hash()`
- `python -m pytest tests/integration/test_api_jobs.py tests/unit/test_s3_runtime_adapters.py tests/unit/test_process_job_failures.py tests/smoke/test_worker_process_job.py -q` -> `11 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed
- `git diff --check` -> passed with CRLF warnings only

## 2026-06-23 Faster ML Polling And Warm Capability Cache

- changed the worker/application default async ML polling interval from `1000` ms to `200` ms
- updated `.env.shadowgen.example`, `.env.example`, and `.env.prod.example` to expose `POLL_INTERVAL_MS=200`
- changed worker composition so `MLCorePipelineAdapter` is reused per effective ML URL instead of being recreated for every business job
- runtime ML URL overrides still create a new adapter because the cache key is the resolved effective ML URL
- added `tests/unit/test_worker_runtime_composition.py` to cover adapter reuse and cache invalidation on effective URL changes
- updated worker/runtime docs and `work/now/latency-analysis.md` to describe the new polling default and warm capability cache behavior
- `python -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/smoke/test_worker_process_job.py tests/unit/test_worker_runtime_composition.py -q` -> `12 passed`
- `python -m pytest tests/unit/test_worker_loop_resilience.py -q` -> `3 passed`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed

## 2026-06-23 Latency Analysis

- inspected web submit, timer, polling, and result rendering paths
- inspected API create/get/result and asset upload/content routes
- inspected worker loop, queue receive/visibility behavior, ML-core submit/poll, and S3-backed job/asset stores
- live `GET https://api.shadowgen.solofarm.ru/v1/system/diagnostics` returned recent jobs matching the supplied screenshots
- live samples showed worker duration over ML `total_ms` of roughly 1.3-2.2 seconds, averaging about 1.8 seconds across six recent jobs
- live samples showed `ml_poll` over ML `total_ms` of roughly 0.6-1.1 seconds in most jobs, matching the 1000 ms worker ML poll interval
- live `ml_probe` stages were roughly 180-237 ms, and the current worker creates a fresh ML-core adapter per job, so its capability cache is not reused across business jobs
- a second live diagnostics request timed out after 20 seconds, consistent with the expensive diagnostics path that lists many Object Storage job JSON records
- wrote the detailed analysis and recommended optimization order in `work/now/latency-analysis.md`

## 2026-06-20 Lost Job Cleanup UI Fix

- live `DELETE https://api.shadowgen.solofarm.ru/v1/jobs/bf1d86cd-3d11-4e2e-984d-82923566ce32` without `X-Admin-Token` returned `401 Invalid admin token`, proving the public API route is reachable and admin-protected
- live CORS preflight for `DELETE /v1/jobs/{job_id}` from `https://shadowgen.solofarm.ru` returned allowed method/header values
- web API client now includes FastAPI `detail` text in thrown errors, so cleanup failures show `401: Invalid admin token` instead of a bare status code
- page-level operator callbacks now rethrow mutation failures after setting the global error, allowing Engineering panel to render per-job failure text
- Engineering lost-job cards now validate that an admin token is present before marking/deleting
- Engineering lost-job cards now show inline pending/success/error status per job
- successfully marked/deleted lost-job cards are hidden immediately while diagnostics refreshes

## 2026-06-20 Lost Job Cleanup UI Checks And Deployment

- `.\.venv\Scripts\python.exe -m pytest tests\integration\test_api_jobs.py tests\integration\test_system_diagnostics_failures.py -q -p no:cacheprovider` -> `7 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-1 .` -> passed
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-1` -> pushed digest `sha256:a4ee03b45ec0e04339aed33e58f03f0c6227dd70491770fdb5d66fda3b9d9057`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-1 ...` -> active revision `bbanh6qrk6qfv0pm6egn`
- `curl.exe -I https://shadowgen.solofarm.ru` -> HTTP `200`
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` -> `{"status":"ok"}`
- live diagnostics after deploy still showed three lost jobs, which is expected until the operator retries cleanup with a valid admin token

## 2026-06-20 Request Cache Clear Button

- added admin-protected `POST /v1/jobs/cache/clear`
- request-cache clearing removes cache keys from job metadata and deletes cache index entries without deleting jobs, source assets, or result artifacts
- memory, file, and S3 job repositories now implement `clear_request_cache()`
- Engineering panel now includes `Clear request cache` with admin-token validation, confirmation, and inline status/error feedback
- web API client parses FastAPI error details for cache cleanup just like other operator mutations

## 2026-06-20 Request Cache Clear Checks And Deployment

- `.\.venv\Scripts\python.exe -m pytest tests\integration\test_api_jobs.py tests\unit\test_s3_runtime_adapters.py -q -p no:cacheprovider` -> `7 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260620-2 .` -> passed
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-2 .` -> passed
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260620-2` -> pushed digest `sha256:0f21506477c5b3b6b7da832a59db0261649646737122cad3ba513447069677e7`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-2` -> pushed digest `sha256:79a85889bcca94d1aeb785a10ae0931cfe2d9c4a253b7b6cd190e16276f4a302`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260620-2 ...` -> active revision `bba467i99b4ph5e6rrh7`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260620-2 ...` -> active revision `bbaiihrmaml52aanpsst`
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` -> `{"status":"ok"}`
- `curl.exe -I https://shadowgen.solofarm.ru` -> HTTP `200`
- `POST https://api.shadowgen.solofarm.ru/v1/jobs/cache/clear` without admin token -> `401 Invalid admin token`
- CORS preflight for `POST /v1/jobs/cache/clear` from `https://shadowgen.solofarm.ru` allowed `x-admin-token`
- full `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` with workspace-local temp -> `50 passed, 1 skipped`
- `powershell -ExecutionPolicy Bypass -File scripts\docs-check.ps1` -> passed
- `git diff --check` -> passed

## 2026-06-19 New ML Service Auto-Detection

- worker capability DTOs now accept the current ML-service handshake fields, including `supported_submit_modes`, `preferred_submit_mode`, `degraded`, and `backends[*].backend_kind`
- a successful `/health` plus `/v1/capabilities` handshake always selects the new ML-core adapter and never probes `/test`
- legacy mode now requires `/test` to return 2xx; `/test` 404 is no longer treated as a healthy legacy service
- sync ML-core mode uses `POST /v1/render`; async mode uses `POST /v1/render/jobs` and polls `GET /v1/render/jobs/{job_id}`
- async statuses `pending`, `running`, `completed`, `failed`, and `cancelled` are supported
- worker sends the durable business `job_id` as ML `request_id`, preventing different renders of one source asset from collapsing under ML idempotency
- `shadow.model` is forwarded unchanged, including `v2-diff`
- ML stage metrics are preserved in job results and shown in expanded Engineering diagnostics

## 2026-06-20 ML-Core Pipeline Version Hotfix

- worker-to-ML-core mapping now always sends `pipeline_version="ml-shadowgen-v1"` to the new ML service
- `shadow.model` remains the only model-family selector for `v1-gan` / `v2-diff`
- the public job DTO's legacy pipeline field is no longer forwarded into the ML-core request contract
- docs now state that `pipeline_version` identifies the ML-core transport contract, not the GAN/diffusion family

## 2026-06-20 ML-Core Pipeline Version Checks

- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_ml_core_adapter.py tests\unit\test_legacy_http_adapter.py -q -p no:cacheprovider` -> `10 passed`

## 2026-06-20 Worker/ML Diagnostics Tightening

- live `http://192.168.1.8:9001/health` returned `status=ok`, `async_enabled=true`, `accepting_jobs=true`
- live `http://192.168.1.8:9001/v1/capabilities` returned the new service shape with `preferred_submit_mode=async`, `degraded=false`, and `shadow_generator` model variant `v2-diff`
- live `http://192.168.1.8:9001/test` returned `404`, which confirms this endpoint must be treated as new ML-core rather than legacy
- direct async submit with `pipeline_version=ml-shadowgen-v1` was accepted and returned `status=pending`, proving the current ML service accepts the corrected worker contract
- the direct tiny-image smoke then returned async `status=failed` with ML error text, so worker diagnostics now preserve async terminal errors on the `ml_poll` stage
- ML submit HTTP failures now include endpoint method/path, HTTP status, ML error code, and message
- process-job observer now classifies failures by the actual failed trace stage, so worker state separates `last_submit_error` and `last_poll_error`
- web Engineering diagnostics now renders `Last ML submit error` and `Last ML poll error`

## 2026-06-20 Worker/ML Diagnostics Checks

- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_ml_core_adapter.py tests\unit\test_process_job_failures.py tests\unit\test_worker_state_service.py tests\unit\test_worker_control_app.py -q -p no:cacheprovider` -> `16 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- first full `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` hit `PermissionError` creating pytest temp data under `C:\Users\solofarm\AppData\Local\Temp\pytest-of-solofarm`
- rerun full pytest with `TEMP` and `TMP` pointed at a workspace-local `.tmp` directory -> `48 passed, 1 skipped`
- `powershell -ExecutionPolicy Bypass -File scripts\docs-check.ps1` -> passed
- `git diff --check` -> passed

## 2026-06-19 New ML Service Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_ml_core_adapter.py tests/unit/test_legacy_http_adapter.py tests/unit/test_process_job_failures.py tests/smoke/test_worker_process_job.py -q -p no:cacheprovider` -> `13 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` -> `46 passed, 1 skipped`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed
- direct `localhost:9001` handshake was not available from this workspace session, so live render was not exercised

## 2026-06-19 Worker UI ML URL Update

- local worker control now exposes token-protected `PUT /api/runtime-config`
- the worker dashboard includes an editable ML URL field and `Save ML URL` button
- saving updates the shared runtime override and immediately republishes the effective ML URL into worker state
- unauthorized runtime-config updates return HTTP `401`
- the change applies to subsequent worker jobs and capability probes

## 2026-06-19 Worker UI ML URL Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_control_app.py tests/unit/test_worker_state_service.py -q` -> `6 passed`
- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` -> `42 passed, 1 skipped`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` -> passed

## 2026-05-26 Stuck Running Job Visibility And Cache Fix

- Live diagnostics showed the worker was fresh and `idle`, YMQ had `queued=0` and `in_flight=0`, while the UI could still display a `running` job.
- `CreateJobUseCase` now reuses `queued` / `running` cache records only while they are fresh; stale live cache records are ignored after 300 seconds and a new queued job is created.
- `GET /v1/system/diagnostics` now scans a wider job window and prioritizes active `queued` / `running` jobs before completed history.
- The result view now shows a long-running warning after one minute and exposes a copyable job id in both compact and full modes.

## 2026-05-26 Stuck Running Job Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_create_job.py tests/integration/test_system_diagnostics_failures.py -q`
- `cmd /c npm run build` in `apps/web`
- `.\.venv\Scripts\python.exe -m pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`

## 2026-05-26 Lost Job Cleanup

- diagnostics now separates stale live metadata into `lost_jobs`
- each lost job includes age, a reason, and concrete evidence such as missing worker current/in-flight state, idle worker status, and empty queue counters
- operator API can mark a job failed through `POST /v1/jobs/{job_id}/mark-failed`
- operator API can delete job metadata and matching request-cache index through `DELETE /v1/jobs/{job_id}`
- web engineering panel renders lost jobs separately from recent jobs with `Mark failed`, `Delete metadata`, and `Copy job id`
- both cleanup actions require `X-Admin-Token`

## 2026-05-26 Lost Job Cleanup Checks

- `.\.venv\Scripts\python.exe -m pytest tests/integration/test_api_jobs.py tests/integration/test_system_diagnostics_failures.py tests/unit/test_create_job.py -q`
- `cmd /c npm run build` in `apps/web`
- `.\.venv\Scripts\python.exe -m pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`

## 2026-05-26 Lost Job Cleanup Cloud Deployment

- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260526-2 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260526-2 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260526-2`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260526-2`
- `yc serverless container revision deploy` activated API revision `bba2giej0k6i3iil36su` with image `shadowgen-api:20260526-2`.
- `yc serverless container revision deploy` activated web revision `bba852878p2ms545dmdu` with image `shadowgen-web:20260526-2`.
- `cmd /c scripts\deploy-yc-shadowgen.cmd` refreshed API and web gateway specs.
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` returned `{"status":"ok"}`.
- `curl.exe -I https://shadowgen.solofarm.ru` returned HTTP `200`.
- live diagnostics returned `lost_jobs` with three lost records; the top record included evidence that the worker is idle and queue has no queued or in-flight messages.

## 2026-05-26 Stuck Running Job Cloud Deployment

- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260526-1 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260526-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260526-1`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260526-1`
- `yc serverless container revision deploy` activated API revision `bbasb5q21q30clln7gke` with image `shadowgen-api:20260526-1`.
- `yc serverless container revision deploy` activated web revision `bbadudle7lr7regjlv4q` with image `shadowgen-web:20260526-1`.
- `cmd /c scripts\deploy-yc-shadowgen.cmd` refreshed API and web gateway specs.
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` returned `{"status":"ok"}`.
- `curl.exe -I https://shadowgen.solofarm.ru` returned HTTP `200`.
- Live diagnostics after deploy showed current active job `5d3a5f17-98f7-4405-8c85-1cfbf5ce0a00` first in `recent_jobs` with status `running`, while queue counts were zero and worker status was `idle`.

## 2026-05-26 Worker Container Script Consolidation

- `scripts/run-worker-cloud-container.cmd` is now the only worker container launcher.
- The remaining script builds `shadowgen-worker-local`, removes any previous `shadowgen-worker`, and starts a detached self-contained container with Docker `--restart unless-stopped`.
- The removed script variants were `scripts/run-worker-cloud-container-detached.cmd` and `scripts/run-worker-cloud-container-self-managed.cmd`.
- The supported container mode does not mount the repository or Docker socket, and worker self-management stays disabled.
- README, overview docs, reference docs, and `.env.shadowgen.example` now point to the single script.

## 2026-05-26 Worker Container Script Checks

- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `git diff --check`
- `rg -n "run-worker-cloud-container-detached|run-worker-cloud-container-self-managed|self-managed" README.md docs scripts .env.shadowgen.example` returned no matches.

## 2026-05-25 Diagnostics Trace And Probe Checks

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_create_job.py tests/unit/test_process_job_failures.py tests/unit/test_worker_state_service.py tests/unit/test_worker_control_app.py tests/integration/test_worker_action_api.py tests/integration/test_system_diagnostics_failures.py tests/smoke/test_worker_process_job.py -q`
- `.\.venv\Scripts\python.exe -m pytest`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`

## 2026-05-25 Diagnostics Trace And Probe Results

- job records now carry compact diagnostic trace stages with durations, messages, and errors
- create-job responses now expose `cache_status` and `reused_existing_job`
- process-job records worker claim, asset loading, ML probe/submit/poll, artifact storage, completion, failure, and terminal no-op stages
- system diagnostics now treats worker heartbeat as stale after five minutes
- worker runtime state now stores last worker probe and last ML probe results
- cloud worker actions and local worker control accept `diagnostic_probe`
- worker-side diagnostic probe uses the effective ML URL and existing ML-core health or legacy `/test` compatibility path
- web engineering panel now shows worker life status, probe status, recent jobs with datetime, micro preview, cache badge, copyable job id, and expandable timelines
- local worker control page now exposes recent job timelines, copyable job ids, worker life indicator, and probe button

## 2026-05-25 Cloud Deployment

- Docker Desktop was started because the local Docker daemon was not running.
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260525-1 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260525-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260525-1`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260525-1`
- `yc serverless container revision deploy` activated API revision `bbajmtej58mtobdjlalj` with image `shadowgen-api:20260525-1`.
- `yc serverless container revision deploy` activated web revision `bbaf2ktsfvumo2g8uluh` with image `shadowgen-web:20260525-1`.
- `cmd /c scripts\deploy-yc-shadowgen.cmd` refreshed API and web gateway specs.
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` returned `{"status":"ok"}`.
- `curl.exe -I https://shadowgen.solofarm.ru` returned HTTP `200`.
- `GET https://api.shadowgen.solofarm.ru/v1/system/diagnostics` returned the new diagnostics fields, including `heartbeat_is_stale`, `last_worker_probe`, and `last_ml_probe`.

## 2026-05-13 Architecture Remediation Checks

- `python -m pytest tests/unit/test_architecture_boundaries.py tests/unit/test_worker_control_app.py tests/integration/test_ymq_adapter.py tests/unit/test_process_job_failures.py tests/unit/test_job_entity.py -q`
- `python -m pytest tests/unit/test_worker_loop_resilience.py tests/integration/test_runtime_config_api.py tests/integration/test_worker_action_api.py tests/integration/test_api_jobs.py tests/integration/test_local_file_runtime.py tests/integration/test_system_diagnostics_failures.py -q`
- `python -m pytest`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`

## 2026-05-13 Architecture Remediation Results

- mutating public API system endpoints now require `X-Admin-Token`
- read-only diagnostics and runtime-config reads remain public
- the web engineering panel now asks the operator for the admin token and does not bake that token into the public build
- API diagnostics no longer constructs or probes `MLCorePipelineAdapter`; it uses worker-published runtime/capability state
- queue adapters now expose delivery envelopes with `ack`, `nack`, and visibility extension hooks
- YMQ messages are deleted only on delivery `ack`; failed handling can `nack` the delivery for redelivery
- the worker loop now receives deliveries and acknowledges them only after job handling completes
- domain job status/lifecycle logic no longer imports public `shadowgen_contracts`
- process-job orchestration routes start/complete/fail transitions through domain lifecycle methods
- redelivery of already terminal jobs is treated as an idempotent no-op
- worker `/api/status` no longer embeds base64 result previews; recent jobs expose a preview URL instead
- worker preview bytes are served by `GET /api/jobs/{job_id}/preview`
- architecture boundary tests now guard against domain-to-contract imports and API-side ML adapter imports
- CI now runs Python tests, web build, and API/worker Docker smoke builds

## What Was Checked

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_state_service.py tests/unit/test_worker_loop_resilience.py tests/unit/test_s3_runtime_adapters.py -q`
- repository rebuilt toward the target api-worker-pipeline-adapter architecture
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `python -m pytest`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_legacy_http_adapter.py tests/smoke/test_worker_process_job.py`
- `npm run build` in `apps/web`
- `.\.venv\Scripts\python.exe -m pytest tests/integration/test_api_jobs.py tests/integration/test_runtime_config_api.py tests/integration/test_system_diagnostics_failures.py tests/integration/test_local_file_runtime.py tests/unit/test_s3_runtime_adapters.py tests/unit/test_legacy_http_adapter.py tests/smoke/test_worker_process_job.py`
- `.\.venv\Scripts\python.exe -m pytest tests/integration/test_runtime_config_api.py tests/integration/test_system_diagnostics_failures.py tests/unit/test_s3_runtime_adapters.py`
- `.\.venv\Scripts\python.exe` config instantiation for `ApiConfig` and `WorkerConfig` against `.env.shadowgen`
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260402-2 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260402-2 .`
- `docker push` for the `shadowgen-api:20260402-2` and `shadowgen-web:20260402-2` images
- `yc serverless container revision deploy` for `shadowgen-api` and `shadowgen-web`
- `curl https://api.shadowgen.solofarm.ru/health`
- `curl -I https://d5d221gjotatrurllmid.k1mxzkh0.apigw.yandexcloud.net`
- `yc serverless api-gateway add-domain shadowgen-web-gw --domain shadowgen.solofarm.ru --certificate-id fpq08aquao87ah8mhrh5`
- `curl -I https://shadowgen.solofarm.ru`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_loop_resilience.py`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_loop_resilience.py tests/unit/test_s3_runtime_adapters.py tests/unit/test_worker_control_app.py tests/integration/test_runtime_config_api.py tests/integration/test_system_diagnostics_failures.py tests/integration/test_worker_action_api.py tests/smoke/test_worker_process_job.py -q`
- `.\.venv\Scripts\python.exe -m pytest`
- `docker build -f apps/worker/Dockerfile -t shadowgen-worker-local .`
- `Resolve-DnsName GTX6`
- `Test-NetConnection 192.168.1.5 -Port 9001`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_legacy_mapper.py tests/unit/test_legacy_http_adapter.py`
- `npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_ml_core_adapter.py tests/unit/test_worker_state_service.py tests/unit/test_worker_loop_resilience.py tests/smoke/test_worker_process_job.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/integration/test_api_jobs.py tests/integration/test_system_diagnostics_failures.py tests/integration/test_runtime_config_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_process_job_failures.py tests/unit/test_ml_core_adapter.py tests/unit/test_worker_state_service.py tests/unit/test_worker_loop_resilience.py tests/smoke/test_worker_process_job.py tests/integration/test_api_jobs.py tests/integration/test_system_diagnostics_failures.py tests/integration/test_runtime_config_api.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_control_app.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_architecture_boundaries.py -q`
- `cmd /c npm run build` in `apps/web`
- `cmd /c npm run build` in `apps/web` after adding client-side latency timing chips
- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_worker_control_app.py -q`
- `Select-String -Path scripts\run-worker-cloud-container.cmd -Pattern "-v |/workspace|docker.sock|WORKER_SELF_MANAGE_ENABLED=true"`
- `docker build --build-arg SHADOWGEN_GIT_BRANCH=local-check --build-arg SHADOWGEN_GIT_COMMIT=local-check -f apps\worker\Dockerfile -t shadowgen-worker-local:self-contained-check .`
- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_s3_runtime_adapters.py tests\unit\test_create_job.py tests\integration\test_api_jobs.py -q`
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260414-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260414-1`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260414-1 ...`
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` after the documentation refresh for the ML-core worker refactor
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_worker_control_app.py tests/unit/test_create_job.py tests/integration/test_api_jobs.py tests/integration/test_local_file_runtime.py -q`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` after documenting request-cache reuse and recent-job previews
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_create_job.py tests/integration/test_api_jobs.py tests/integration/test_local_file_runtime.py tests/unit/test_s3_runtime_adapters.py -q`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` after documenting the metadata-driven cache fast path
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-1 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-1`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-1`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-1 ...`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-1 ...`
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-2 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-2`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-2 ...`
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-3 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-2 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-3`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-2`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260413-3 ...`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260413-2 ...`
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health`
- local worker image rebuild and detached container restart with `shadowgen-worker-local`
- `Invoke-RestMethod http://localhost:8081/api/status | ConvertTo-Json -Depth 6`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260414-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260414-1`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260414-1 ...`
- `curl.exe -I https://shadowgen.solofarm.ru`

## What Is Confirmed By Code

- worker idle polling no longer rewrites `runtime/worker-state.json` on every empty queue poll
- worker runtime state is cached in-process and published on meaningful state changes, runtime-config override changes, or the throttled idle heartbeat interval
- the default idle heartbeat interval is 30 seconds, which cuts S3/Object Storage `PUT` volume without crossing the current 60-second stale heartbeat threshold used by diagnostics
- FastAPI app exposes `GET /health`
- `POST /v1/assets` uploads a source asset and returns a v2 asset reference
- `POST /v1/jobs` creates a queued job using v2 contracts
- `GET /v1/jobs/{job_id}` returns job metadata
- `GET /v1/system/diagnostics` exposes engineering-safe diagnostics, including storage backend and worker heartbeat freshness
- worker-side `ProcessJobUseCase` can complete a job through `LegacyPipelineAdapter`
- file-backed local adapters support separate API/worker runtime instances
- S3/Object Storage-backed adapters exist for assets, jobs, runtime config, and worker state
- YMQ adapter exists behind the queue port and is covered by contract-style tests
- runtime config accepts unified uppercase storage env names `S3_ENDPOINT_URL`, `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY`
- `.env.shadowgen` has been populated from the existing `.env`, and a dedicated YMQ queue URL for ShadowGen is configured
- legacy integration is isolated under `packages/adapters/src/shadowgen_adapters/legacy_pipeline`
- legacy `rot` is serialized as an integer string so old `ShadowGEN` parsing does not silently fall back to `0`
- user UI keeps the last successful result preview visible while a new job is running and shows a live processing timer
- user UI auto-submits a refreshed job after debounced angle changes and keeps the result preview layout stable while status and timer update
- engineering UI uses compact ML server controls and separates queue state and recent jobs into dedicated subpanels apart from runtime and worker parameters
- API and worker runtime config now read from `.env.shadowgen`
- local `api` and `web` container entrypoints exist for cloud-shaped development
- local `worker` can be launched either directly from the host or from a dedicated local Docker image using `.env.shadowgen`
- the ML service is reachable on `192.168.1.5:9001`, and the previous container-side `GTX6` lookup failure was a hostname resolution issue rather than an ML-server outage
- worker runtime now exposes a local FastAPI control app with HTML and JSON endpoints on the worker control port
- worker diagnostics now include effective ML URL, last completed duration, recent completed jobs, and recent worker actions
- cloud API can enqueue worker control actions through `POST /v1/system/worker-actions`
- cloud frontend engineering panel can request worker restart/update/clear-override actions without direct inbound access to the worker host
- worker container build now includes `git`, Docker SDK support, and self-management runtime settings
- the worker local control page now shows recent successful jobs with second-precision completion timestamps and inline preview data URLs when the final asset can be fetched directly from the active asset store
- recent-job previews fail quietly when an old or missing result asset cannot be fetched, so the diagnostics page stays usable without extra recovery logic
- the currently running local `shadowgen-worker` container has been rebuilt and restarted on the refreshed image, and `/api/status` now returns `recent_completed_jobs[*].finished_at_display` plus `preview_src`
- a clean target contract for the future non-legacy ML service is documented separately from the legacy adapter contract
- the v2 render contract now includes `shadow.elevation_deg` for light elevation above the horizon
- the web UI now submits both shadow direction and light elevation while preserving the existing auto-submit flow
- the legacy adapter now sends only legacy-supported fields to the old ML service and ignores v2-only shadow parameters
- worker/core integration now uses a dedicated ML-core adapter boundary with `probe`, `submit`, `poll`, and `cancel`
- the worker can discover ML-core async support through `/health` and `/v1/capabilities`, and it falls back to legacy sync mode when only the old ShadowGEN transport is available
- the business render contract now includes `preprocess.padding_px`, which is mapped only at the worker/core boundary and does not reshape the public jobs API
- the worker loop now supports bounded in-flight business jobs instead of a strict single-flight execution model
- worker runtime state now carries ML-core mode, async flag, capability snapshot, in-flight jobs, and capability refresh diagnostics
- engineering diagnostics now expose ML-core mode, async support, in-flight count, and capabilities refresh metadata
- the cloud engineering panel now renders ML-core mode, fallback state, capability refresh details, and current in-flight jobs
- overview and reference documentation now explicitly describe the `web/api -> queue/state -> worker -> ML core` runtime shape and the `probe/submit/poll/cancel` worker/core boundary
- reference docs now mention the `ml_core/` adapter package and the worker/ML-core orchestration config keys
- the root README and `docs/` tree now reflect the current cloud-shaped runtime instead of earlier bootstrap-only framing
- the docs tree now has an overview layer plus a module-by-module reference layer for all active top-level apps and packages
- job creation now derives a request cache key from source image bytes plus a normalized render request payload rather than raw `source_asset_id`
- request-cache normalization ignores `source_asset_id`, so re-uploading the same binary image with the same render settings can reuse an existing job
- duplicate `queued`, `running`, and `succeeded` jobs are short-circuited before queue publish, while `failed` and `canceled` jobs still allow a fresh retry
- request-cache lookup no longer needs to download the full source image on cache hit when the asset metadata already contains `source_hash`
- file and S3 job repositories now keep a direct request-cache index, so cache-hit lookup no longer scans all stored job records
- the API create-job path now reuses a source hash computed before the use case call, so it avoids a second storage metadata read for the same source asset
- the web UI now reuses the uploaded `source_asset_id` for the currently selected file instead of re-uploading the same file on every parameter tweak or repeated submit
- the web UI now reuses the in-memory completed job immediately when a cache hit returns the same `job_id`, instead of fetching that same job again before showing the result
- the user-page job polling interval was reduced from 1500 ms to 350 ms, which removes roughly a second of average wait after fast worker completions
- asset content responses are now marked `Cache-Control: public, max-age=31536000, immutable`, so browsers can reuse immutable result asset responses by asset ID
- the user result panel now exposes client-side latency timings for upload reuse, create-job latency, first get/poll latency, cache hit/miss, job-visible time, and image-visible time
- the default worker container script now runs the worker without bind-mounting the host repository into `/workspace`
- the default worker container script now runs without mounting `/var/run/docker.sock`, so the worker no longer has host-level Docker control in the normal runtime
- `scripts/run-worker-cloud-container-self-managed.cmd` preserves the previous self-managed update mode as an explicit opt-in path for local operator experiments
- worker image builds with `SHADOWGEN_GIT_BRANCH` and `SHADOWGEN_GIT_COMMIT` build args so self-contained containers can still report version metadata without a mounted `.git` directory
- the worker local control UI now reports container mode and disables `Update from git` when self-management is disabled
- S3/Object Storage request-cache lookup is now index-only on the `POST /v1/jobs` hot path; a cache-index miss no longer scans every `jobs/*.json` object
- the shared render and ML-core contracts now carry `shadow.model` with `v1-gan` / `v2-diff`, and the ML-core request source payload now uses `image_base64`
- the web UI now has a phone-first vertical basic flow with model selection plus an `Advanced` mode that preserves the previous manual shadow controls
- the basic user flow now hides ineffective manual shadow controls for `v2-diff` while still keeping the broader product request and adapter boundary intact
- the web shell now switches between `Min`, `Max`, and `Engineering`, with `Top` / `Side` model pills at the top and the compact `Min` composition aligned to `design/ref`
- the source preview area now doubles as the upload/camera entry point in `Min`, and loaded source previews now expose a small clear button for quick replacement
- the compact result panel in `Min` now keeps the preview stable and shows only the tight bottom metadata row (`time`, `status`, `save`) so the mobile layout stays dense without reflow
- `api.shadowgen.solofarm.ru` is attached to Yandex API Gateway and responds through the deployed serverless container
- `shadowgen.solofarm.ru` is attached to the web API Gateway and responds through the deployed serverless container
- the default web gateway domain responds through the deployed serverless container after switching both Docker images to the runtime `PORT`
- the active serverless revisions are now `shadowgen-api:20260413-1` and `shadowgen-web:20260413-1`
- the active API serverless revision is now `shadowgen-api:20260413-2`, which includes the metadata-driven request-cache fast path
- the active serverless revisions are now `shadowgen-api:20260413-3` and `shadowgen-web:20260413-2`, which include the cache-hit latency reductions and faster user-page polling path
- the active web serverless revision is now `shadowgen-web:20260414-1` (`bbabuhrm325vf8gskkoe`), which includes the client-side latency timing panel
- the active API serverless revision is now `shadowgen-api:20260414-1` (`bbakfnnvte9du1984i6g`), which removes S3 full job scans from request-cache misses
- `powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1` passed before the 2026-04-28 rollout
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260428-1 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-1 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260428-1`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-1`
- `yc serverless container revision deploy --container-name shadowgen-api --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260428-1 ...`
- `yc serverless container revision deploy --container-name shadowgen-web --image cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-1 ...`
- `cmd /c scripts\\deploy-yc-shadowgen.cmd` refreshed both API Gateway specs after the new revisions were deployed
- the active API serverless revision is now `shadowgen-api:20260428-1` (`bba1mm6asj40oh6orbei`)
- the active web serverless revision is now `shadowgen-web:20260428-1` (`bbaof6jeqik3akoi2gdn`)
- `https://api.shadowgen.solofarm.ru/health` responded with `{"status":"ok"}`
- `https://shadowgen.solofarm.ru` responded with HTTP `200` and served the `Shadow Generator` page
- `powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1` passed before the `20260428-2` rollout
- `docker build -f apps/api/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260428-2 .`
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-2 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-api:20260428-2`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-2`
- `yc serverless container revision deploy` activated `shadowgen-api:20260428-2` as revision `bba9l44jgba57vcsg47e`
- `yc serverless container revision deploy` activated `shadowgen-web:20260428-2` as revision `bbaa9jppfh6h4fsasq5i`
- `cmd /c scripts\\deploy-yc-shadowgen.cmd` refreshed both API Gateway specs after the `20260428-2` revisions were deployed
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` responded with `{"status":"ok"}`
- `curl.exe -I https://shadowgen.solofarm.ru` responded with HTTP `200`
- `Invoke-WebRequest https://shadowgen.solofarm.ru` returned the deployed Next.js HTML document
- `powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1` passed before the mini UI width hotfix rollout
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-3 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-3`
- `yc serverless container revision deploy` activated `shadowgen-web:20260428-3` as revision `bba06p5d2se36ekr6c7a`
- `curl.exe -I https://shadowgen.solofarm.ru` responded with HTTP `200` after the mini UI width hotfix
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` still responded with `{"status":"ok"}`
- `powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1` passed before the client-side upload resize rollout
- `docker build --build-arg NEXT_PUBLIC_API_BASE=https://api.shadowgen.solofarm.ru -f apps/web/Dockerfile -t cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-4 .`
- `docker push cr.yandex/crpal081a5mju2k2amfn/shadowgen-web:20260428-4`
- `yc serverless container revision deploy` activated `shadowgen-web:20260428-4` as revision `bbavmmte04p2ht1qtgva`
- `curl.exe -I https://shadowgen.solofarm.ru` responded with HTTP `200` after the client-side upload resize rollout
- `curl.exe -fsS https://api.shadowgen.solofarm.ru/health` still responded with `{"status":"ok"}`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` passed after adding the permanent worker host deployment guide
- `Select-String -Path scripts\\run-worker-cloud-container-detached.cmd -Pattern "--restart unless-stopped|-d \\^|-v |docker.sock|WORKER_SELF_MANAGE_ENABLED=false|--env-file .env.shadowgen"` confirmed detached restart-policy launch, env-file usage, disabled self-management, and no repository/Docker-socket mounts
- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_worker_state_service.py tests\unit\test_worker_control_app.py -q` passed after clearing stale capability diagnostics when the effective ML URL changes
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` passed after documenting ML URL override priority
- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_ml_core_adapter.py tests\unit\test_worker_control_app.py tests\unit\test_worker_state_service.py tests\unit\test_legacy_mapper.py tests\unit\test_legacy_http_adapter.py -q` passed after treating reachable old ML service as legacy compatibility mode instead of degraded capability failure
- `cmd /c npm run build` in `apps/web` passed after disabling `Side` mode when diagnostics report `legacy-sync`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1` passed after documenting `LEGACY_ML_HOST_IP_OVERRIDE`
- Yandex Cloud resources now exist for ShadowGen: Object Storage bucket `shadowgen.solofarm.ru`, YMQ queue `shadowgen-v2-render-jobs`, container registry `shadowgen-v2`, API gateways for `api` and `web`
- architecture boundary tests enforce clean/hexagonal separation rules

## What Is Still Assumed

- exact Yandex serverless deployment wrapper and CI publish flow
- exact legacy deployment URL and auth shape
- whether future metadata remains bucket-only or later moves to a database

## What Was Updated

- worker runtime state publishing logic
- ML-core DTOs and worker/core mapping logic
- process-job orchestration around capabilities probing, submission, and async polling
- worker loop bounded in-flight execution
- worker diagnostics, state model, and engineering UI for ML-core execution state
- worker heartbeat configurability via `WORKER_STATE_HEARTBEAT_INTERVAL_SEC`
- worker reference docs for throttled S3-backed heartbeat behavior
- ML-core contract docs and worker module reference docs for dual sync/async orchestration
- overview and module reference docs for the post-refactor ML-core runtime shape
- targeted unit coverage for idle heartbeat throttling and idempotent boot publishing
- repository structure
- contracts
- domain and application packages
- pipeline interfaces
- API, worker, and web skeletons
- file, memory, and S3/Object Storage runtime adapters
- YMQ queue adapter
- legacy adapter boundary
- local containerization for `apps/api` and `apps/web`
- runtime env split into `.env.shadowgen`
- worker container entrypoint and local worker-container run script
- worker control plane contracts, stores, API routes, local UI, and self-managed container helper flow
- legacy secret naming preserved for storage credentials and defaults
- worker container launch now resolves the ML hostname from `LEGACY_ML_BASE_URL` and injects it into Docker host aliases when needed
- worker recent-job diagnostics payload and local dashboard layout
- duplicate-request cache lookup before queue publish in the create-job path
- Yandex Cloud runtime resources and first public deployment
- architecture instructions and boundary docs
- documentation
- the ML-core contract reference and web-module reference docs now describe the `v1-gan` / `v2-diff` split and the mobile-first basic-vs-advanced UI behavior
- `cmd /c npm run build` in `apps/web` passed after the `Min/Max/Engineering` composition refactor
- `.\.venv\Scripts\python.exe -m pytest tests\unit\test_ml_core_adapter.py -q` passed after the web-shell composition refactor
- the web client now downsizes oversized uploaded images before API upload so the shorter side is at most 1024 px, preserving smaller images as-is
- `docs/overview/permanent-worker-host.md` now documents moving the worker to a separate always-on Docker host
- `.env.shadowgen.example` now explains the required worker-host storage, queue, ML, and control-plane values with examples
- `scripts/run-worker-cloud-container-detached.cmd` now starts the self-contained worker container in detached mode with Docker restart policy for permanent host operation
- worker state now clears stale ML capability status and capability refresh errors when the effective ML URL changes
- worker-host docs now state that runtime ML override from shared config has priority over `LEGACY_ML_BASE_URL` in `.env.shadowgen`
- ML-core adapter now treats a reachable old ML service as normal `legacy-sync` compatibility mode rather than a degraded capability issue
- worker control UI now shows timestamps for recent failures so old failures are distinguishable from current failures
- worker container scripts now support `LEGACY_ML_HOST_IP_OVERRIDE` for Docker `--add-host` mapping when the ML URL uses a hostname the container cannot resolve
- web UI now disables `Side` model selection when diagnostics report `legacy-sync`, because the oldest ML service has no model-selection support
- overview pages and module reference pages for active runtime modules
- tracking
- tests

## Remaining Risks

- containerized local flow assumes external Yandex queue/storage endpoints rather than a fully local emulation stack
- live legacy server integration remains environment-dependent and was not exercised in these checks
- container self-update/recreate is an MVP path for the home-server phase and relies on Docker socket + workspace mount conventions remaining stable
- the self-managed worker mode still relies on Docker socket and repository mounts, so it should remain opt-in rather than the default Docker Desktop path

## 2026-06-23 Worker Liveness And Queue Lease Fix

Observed production diagnostics showed a running async job stuck at `ml_poll: running`, repeated `worker_claimed` trace entries, and worker state error `Cannot start job ... from state 'running'; expected 'queued'`. This pointed to YMQ redelivering the same business job while the first worker execution was still waiting for async ML completion.

Updated behavior:

- worker loop extends queue visibility for active deliveries
- duplicate delivery of a locally active job id replaces the active receipt handle instead of starting a second executor
- job failures no longer set worker runtime `status=error`; heartbeat/life now represents worker process freshness, while `last_error`, `last_submit_error`, and `last_poll_error` represent job/ML failures
- local worker UI and web engineering panel now label stale worker state as `stale/probe failed` instead of mixing worker liveness with the last job error
- `.env*` examples document `QUEUE_VISIBILITY_TIMEOUT_SEC` and `QUEUE_VISIBILITY_EXTEND_INTERVAL_SEC`
- worker/runtime docs describe queue lease extension and the separation between worker heartbeat and ML/job errors

Checks:

- `python -m pytest tests\unit\test_worker_loop_resilience.py -q` -> `3 passed`
- `python -m pytest tests\integration\test_api_jobs.py tests\integration\test_system_diagnostics_failures.py tests\unit\test_s3_runtime_adapters.py -q` -> `10 passed`
- `cmd /c npm run build` in `apps/web` -> passed
- `python -m pytest -q` -> `52 passed, 1 skipped`
- `powershell -ExecutionPolicy Bypass -File scripts\docs-check.ps1` -> passed
