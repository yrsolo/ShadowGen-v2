# Evidence

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
- a clean target contract for the future non-legacy ML service is documented separately from the legacy adapter contract
- the v2 render contract now includes `shadow.elevation_deg` for light elevation above the horizon
- the web UI now submits both shadow direction and light elevation while preserving the existing auto-submit flow
- the legacy adapter now sends only legacy-supported fields to the old ML service and ignores v2-only shadow parameters
- the root README and `docs/` tree now reflect the current cloud-shaped runtime instead of earlier bootstrap-only framing
- the docs tree now has an overview layer plus a module-by-module reference layer for all active top-level apps and packages
- `api.shadowgen.solofarm.ru` is attached to Yandex API Gateway and responds through the deployed serverless container
- `shadowgen.solofarm.ru` is attached to the web API Gateway and responds through the deployed serverless container
- the default web gateway domain responds through the deployed serverless container after switching both Docker images to the runtime `PORT`
- Yandex Cloud resources now exist for ShadowGen: Object Storage bucket `shadowgen.solofarm.ru`, YMQ queue `shadowgen-v2-render-jobs`, container registry `shadowgen-v2`, API gateways for `api` and `web`
- architecture boundary tests enforce clean/hexagonal separation rules

## What Is Still Assumed

- exact Yandex serverless deployment wrapper and CI publish flow
- exact legacy deployment URL and auth shape
- whether future metadata remains bucket-only or later moves to a database

## What Was Updated

- worker runtime state publishing logic
- worker heartbeat configurability via `WORKER_STATE_HEARTBEAT_INTERVAL_SEC`
- worker reference docs for throttled S3-backed heartbeat behavior
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
- Yandex Cloud runtime resources and first public deployment
- architecture instructions and boundary docs
- documentation
- overview pages and module reference pages for active runtime modules
- tracking
- tests

## Remaining Risks

- containerized local flow assumes external Yandex queue/storage endpoints rather than a fully local emulation stack
- live legacy server integration remains environment-dependent and was not exercised in these checks
- container self-update/recreate is an MVP path for the home-server phase and relies on Docker socket + workspace mount conventions remaining stable
