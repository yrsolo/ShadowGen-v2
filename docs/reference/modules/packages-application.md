# Application Package

Path:

- `packages/application/src/shadowgen_application`

Purpose:

- hold use cases and ports
- coordinate business flow without depending on infrastructure

Key files:

- `ports.py` - storage, queue, worker-action, and pipeline ports
- `dto.py` - command DTOs
- `use_cases/create_job.py`
- `use_cases/process_job.py`
- `use_cases/upload_asset.py`
- `use_cases/get_system_diagnostics.py`
- `use_cases/create_worker_action.py`
- `use_cases/update_runtime_config.py`

Design rule:

- application depends on contracts, domain, and ports only
- adapter implementations must stay outside this package

Current execution note:

- `ProcessJobUseCase` still operates on one business job at a time
- internally it now performs capability probing plus `submit/poll` orchestration against the pipeline port
- worker state updates are emitted through an observer port so application code does not depend on worker UI or persistence details
