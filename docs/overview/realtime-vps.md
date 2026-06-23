# Realtime VPS Service

This guide describes the standalone realtime accelerator service.

Current status:

- `apps/realtime` exists as a deployable FastAPI service
- it is deployed on the VPS behind `https://rt.shadowgen.solofarm.ru`
- `apps/api` can publish queued-job events and return job-scoped SSE subscription metadata
- `apps/web` can listen to SSE and keeps API polling as fallback
- `apps/worker` can publish worker-seen and terminal lifecycle events
- `apps/worker` can keep an outbound wake stream to interrupt idle sleep after queued-job events
- executable work still comes from YMQ
- Object Storage and YMQ remain the durable production path

## Runtime Role

The realtime service is an optional accelerator for future phases.

It provides:

- `GET /health`
- `POST /internal/v1/jobs/queued`
- `POST /internal/v1/jobs/events`
- `GET /internal/v1/workers/{worker_id}/wake`
- `GET /v1/realtime/jobs/{job_id}/events`

It does not provide:

- job creation
- result or artifact storage
- source image upload
- worker control
- durable queue semantics

## Deployment Name

Recommended VPS layout:

```text
/opt/shadowgen-realtime
container: shadowgen-realtime
image: shadowgen-realtime:latest
port: 8082
```

Public hostname:

```text
https://rt.shadowgen.solofarm.ru
```

Health can be checked through:

```text
https://rt.shadowgen.solofarm.ru/health
```

The container still listens on localhost/VPS port `8082` behind nginx and Let's Encrypt TLS.

## Local Deploy Config

Local `.env` should contain:

```dotenv
DEPLOY_HOST=89.169.132.198
DEPLOY_USER=yrsolo
DEPLOY_PATH=/opt/shadowgen-realtime
SSH_KEY=~/.ssh/id_ed25519
```

`.env` is ignored by git.

## Deploy

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy-realtime-vps.ps1
```

The script:

- packages the current workspace without `.env`, `.git`, virtualenv, node artifacts, and runtime state
- uploads the package to `DEPLOY_PATH`
- extracts it into `DEPLOY_PATH/src`
- creates `DEPLOY_PATH/.env.realtime` with generated secrets if missing
- builds `shadowgen-realtime:latest`
- restarts container `shadowgen-realtime`
- verifies `http://127.0.0.1:8082/health` from the VPS

The script preserves an existing `.env.realtime`, so deployed tokens are not rotated on every deploy.

## Server Environment

Server-local `DEPLOY_PATH/.env.realtime` contains:

```dotenv
APP_ENV=prod
PORT=8082
VPS_PUBLIC_BASE_URL=https://rt.shadowgen.solofarm.ru
VPS_INTERNAL_TOKEN=<generated>
WORKER_VPS_TOKEN=<generated>
VPS_REALTIME_SIGNING_SECRET=<generated>
ALLOWED_ORIGINS=https://shadowgen.solofarm.ru,http://localhost:3000,http://127.0.0.1:3000
EVENT_RETENTION_SEC=300
HEARTBEAT_INTERVAL_SEC=15
```

Do not commit these values.

## API And Worker Settings

API-side settings:

```dotenv
VPS_ACCELERATOR_ENABLED=true
VPS_ACCELERATOR_URL=https://rt.shadowgen.solofarm.ru
VPS_INTERNAL_TOKEN=<same value as server .env.realtime>
VPS_REALTIME_SIGNING_SECRET=<same value as server .env.realtime>
VPS_NOTIFY_TIMEOUT_MS=300
VPS_REALTIME_TOKEN_TTL_SEC=300
VPS_REALTIME_FALLBACK_POLL_MS=350
```

Worker-side settings:

```dotenv
VPS_ACCELERATOR_ENABLED=true
VPS_ACCELERATOR_URL=https://rt.shadowgen.solofarm.ru
WORKER_ID=local-gpu-1
WORKER_VPS_TOKEN=<same value as server .env.realtime>
VPS_EVENT_TIMEOUT_MS=300
VPS_WAKE_ENABLED=true
VPS_WAKE_RECONNECT_MIN_SEC=1
VPS_WAKE_RECONNECT_MAX_SEC=30
```

`VPS_INTERNAL_TOKEN` is for API-to-VPS calls. `WORKER_VPS_TOKEN` is for worker-to-VPS calls. `VPS_REALTIME_SIGNING_SECRET` signs browser subscription tokens.

Wake stream behavior:

- the worker opens an outbound SSE stream to `/internal/v1/workers/{worker_id}/wake`
- the VPS emits `job_wake` after a non-duplicate queued-job signal
- the worker sets a local wake event and immediately returns to its normal queue receive loop
- the worker never executes the `job_id` from the wake command directly

## Safety Notes

- Internal endpoints fail closed when tokens are missing or left as `change-me-*`.
- SSE requires a job-scoped signed token.
- Events do not contain image bytes, artifact bytes, storage credentials, admin tokens, worker control tokens, or private ML details.
- If the service is down, the current API/YMQ/Object Storage/worker path is unaffected.
