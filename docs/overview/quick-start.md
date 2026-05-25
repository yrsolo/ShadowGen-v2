# Quick Start

## Goal

Run the current cloud-shaped system locally with:

- local `web`
- local `api`
- local or containerized `worker`
- Yandex-backed queue and shared storage

## Required Config

Runtime configuration lives in `.env.shadowgen`.

Create it from:

- `.env.shadowgen.example`

Fill at least:

- `STATE_BACKEND`
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `QUEUE_BACKEND`
- `YMQ_ENDPOINT`
- `YMQ_QUEUE_URL`
- `LEGACY_ML_BASE_URL`
- `MAX_IN_FLIGHT_JOBS`
- `POLL_INTERVAL_MS`
- `JOB_TTL_MS`
- `CAPABILITIES_REFRESH_INTERVAL_SEC`

## Main Run Modes

### Local containers for `api` and `web`, worker on host

```powershell
scripts\run-local-containers.cmd
scripts\run-worker-cloud.cmd
```

### Local containers for `api`, `web`, and `worker`

```powershell
scripts\run-local-containers.cmd
scripts\run-worker-cloud-container.cmd
```

`scripts\run-worker-cloud-container.cmd` starts the worker in the preferred stable mode:

- the repository is baked into the image at build time
- the host repository is not bind-mounted into the container
- Docker socket is not mounted into the container
- the container runs detached with `--restart unless-stopped`
- `Update from git` / container self-rebuild actions are disabled

### Permanent Docker worker host

For a separate always-on computer that should keep only the worker running in Docker, use:

```powershell
scripts\run-worker-cloud-container.cmd
```

The same script starts `shadowgen-worker` in detached mode with `--restart unless-stopped`, so Docker restarts it after host or Docker restarts. Full setup instructions are in [Permanent Worker Host](permanent-worker-host.md).

## Useful URLs

- local worker UI: `http://localhost:8081`
- local worker JSON: `http://localhost:8081/api/status`
- public web: `https://shadowgen.solofarm.ru`
- public API health: `https://api.shadowgen.solofarm.ru/health`

## Worker Runtime Notes

- the worker defaults the effective ML URL from its config and only uses runtime override when one is explicitly set
- worker/core execution mode is discovered at runtime from `GET /health` and `GET /v1/capabilities`
- `MAX_IN_FLIGHT_JOBS` controls business-job concurrency only
- batching stays inside the ML core and Triton layer
- the default worker container is self-contained and portable; only `.env.shadowgen`, network access to YMQ/Object Storage, and access to the ML URL are required at runtime
