# Runtime And Scripts

## Runtime Config File

Application runtime config is loaded from `.env.shadowgen`.

Important keys:

- storage:
  - `STATE_BACKEND`
  - `S3_ENDPOINT_URL`
  - `S3_BUCKET`
  - `S3_REGION`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `S3_PREFIX`
- queue:
  - `QUEUE_BACKEND`
  - `YMQ_ENDPOINT`
  - `YMQ_QUEUE_URL`
  - `YMQ_REGION`
  - `QUEUE_VISIBILITY_TIMEOUT_SEC`
  - `QUEUE_VISIBILITY_EXTEND_INTERVAL_SEC`
- ML:
  - `LEGACY_ML_BASE_URL`
  - `LEGACY_ML_HOST_IP_OVERRIDE`
  - `LEGACY_ML_TIMEOUT_SEC`
- worker/ML-core orchestration:
  - `MAX_IN_FLIGHT_JOBS`
  - `SUBMIT_TIMEOUT_MS`
  - `POLL_INTERVAL_MS`
  - `JOB_TTL_MS`
  - `CAPABILITIES_REFRESH_INTERVAL_SEC`
  - `MAX_RETRIES`
- worker control plane:
  - `WORKER_CONTROL_HOST`
  - `WORKER_CONTROL_PORT`
  - `WORKER_CONTROL_TOKEN`
  - `WORKER_STATE_HEARTBEAT_INTERVAL_SEC`
  - `WORKER_SELF_MANAGE_ENABLED`

## Main Scripts

### Local bootstrap

- `scripts/bootstrap.ps1`
- `scripts/install-local-deps.cmd`

### Local runtime

- `scripts/run-local-services.cmd`
- `scripts/run-local-containers.cmd`
- `scripts/run-worker-cloud.cmd`
- `scripts/run-worker-cloud-container.cmd`

### Verification

- `scripts/docs-check.ps1`
- `scripts/release-check.ps1`

### Cloud deployment helper

- `scripts/deploy-yc-shadowgen.cmd`

## Runtime Stores

Depending on config, runtime factories can build:

- file-backed stores
- memory-backed stores
- S3/Object Storage-backed stores

The active wiring is built in:

- `packages/adapters/src/shadowgen_adapters/runtime/factories.py`

## Execution Notes

- `apps/web` and `apps/api` are the public cloud-facing services
- `apps/worker` remains local and owns business-job orchestration
- the worker discovers ML-core sync/async capabilities at runtime
- `POLL_INTERVAL_MS` defaults to 200 ms because the ML service is expected to be local to the worker host; raise it if the ML endpoint becomes remote or rate-sensitive
- `CAPABILITIES_REFRESH_INTERVAL_SEC` defaults to 300 seconds; lower it only when ML-core capabilities change often during operation
- the worker extends queue visibility while an async ML job is running; keep `QUEUE_VISIBILITY_TIMEOUT_SEC` comfortably above the extension interval
- `LEGACY_ML_BASE_URL` remains the effective worker-side ML target variable for now, even when the endpoint is actually the new ML core
- `LEGACY_ML_HOST_IP_OVERRIDE` can force Docker `--add-host` mapping when the ML URL uses a hostname that the container cannot resolve
- `scripts/run-worker-cloud-container.cmd` is the single worker container mode: it builds the worker image, injects git metadata as build args, starts `shadowgen-worker` detached with `--restart unless-stopped`, and runs without mounting the repository or Docker socket
