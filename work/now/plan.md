# Plan

## Steps

1. Configure DNS, nginx, and TLS for `rt.shadowgen.solofarm.ru`.
2. Update and redeploy `apps/realtime` with API queued-event and worker lifecycle-event ingestion.
3. Wire `apps/api` to publish queued events and return job-scoped SSE subscription metadata.
4. Wire `apps/web` to consume SSE with API polling fallback and timing diagnostics.
5. Wire `apps/worker` to publish best-effort worker-seen and terminal lifecycle events.
6. Wire worker wake hints through outbound SSE and a local worker loop wake event.
7. Deploy API/Web container revisions and restart the local worker container with realtime env.
8. Update docs, env examples, and evidence.
9. Run focused/full Python tests, Web build, docs check, and diff checks.

## Checks

- `python -m pytest tests/integration/test_api_jobs.py tests/unit/test_realtime_app.py tests/unit/test_realtime_contracts.py tests/unit/test_worker_runtime_composition.py tests/unit/test_architecture_boundaries.py -q`
- `python -m pytest -q`
- `docker build -f apps/realtime/Dockerfile -t shadowgen-realtime:local .`
- `cmd /c npm run build` in `apps/web`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File scripts/deploy-realtime-vps.ps1`
- public health checks for realtime/API/Web
- worker container env/status check
- wake endpoint and worker listener checks

## Deliverables

- `apps/realtime`
- `apps/realtime/Dockerfile`
- `scripts/deploy-realtime-vps.ps1`
- realtime adapter/signing code
- API/Web/worker integration code
- runtime docs and deployment evidence
