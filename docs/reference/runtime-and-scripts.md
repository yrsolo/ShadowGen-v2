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
- ML:
  - `LEGACY_ML_BASE_URL`
  - `LEGACY_ML_TIMEOUT_SEC`
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
