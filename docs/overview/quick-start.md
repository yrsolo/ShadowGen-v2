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

## Useful URLs

- local worker UI: `http://localhost:8081`
- local worker JSON: `http://localhost:8081/api/status`
- public web: `https://shadowgen.solofarm.ru`
- public API health: `https://api.shadowgen.solofarm.ru/health`
