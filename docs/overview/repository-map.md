# Repository Map

## Main Runtime Paths

- `apps/api/src/shadowgen_api`
- `apps/web/src`
- `apps/worker/src/shadowgen_worker`
- `packages/contracts/src/shadowgen_contracts`
- `packages/application/src/shadowgen_application`
- `packages/domain/src/shadowgen_domain`
- `packages/pipeline/src/shadowgen_pipeline`
- `packages/adapters/src/shadowgen_adapters`

## Where To Look First

### If you work on API behavior

- `apps/api/src/shadowgen_api/main.py`
- `apps/api/src/shadowgen_api/routes/`
- `apps/api/src/shadowgen_api/deps.py`

### If you work on worker behavior

- `apps/worker/src/shadowgen_worker/main.py`
- `apps/worker/src/shadowgen_worker/loop.py`
- `apps/worker/src/shadowgen_worker/control_app.py`
- `apps/worker/src/shadowgen_worker/control_actions.py`

### If you work on UI behavior

- `apps/web/src/app/page.tsx`
- `apps/web/src/components/`
- `apps/web/src/lib/`

### If you work on contracts and business flow

- `packages/contracts/src/shadowgen_contracts/`
- `packages/application/src/shadowgen_application/`
- `packages/domain/src/shadowgen_domain/`
- `packages/pipeline/src/shadowgen_pipeline/`

### If you work on integrations

- `packages/adapters/src/shadowgen_adapters/storage/`
- `packages/adapters/src/shadowgen_adapters/queue/`
- `packages/adapters/src/shadowgen_adapters/runtime/`
- `packages/adapters/src/shadowgen_adapters/legacy_pipeline/`
