# Contracts Package

Path:

- `packages/contracts/src/shadowgen_contracts`

Purpose:

- define shared DTOs, enums, diagnostics models, job contracts, render contracts, and worker-system contracts

Key files:

- `render.py` - render request/result DTOs
- `ml_core.py` - internal worker-to-ML-core DTOs for health, capabilities, sync render, and async jobs
- `jobs.py` - job DTOs and queue message
- `assets.py` - asset refs
- `diagnostics.py` - diagnostics payloads
- `system.py` - runtime config and worker action contracts
- `errors.py` - shared error models
- `enums.py` - shared enums

Important split:

- public product flow still uses `render.py`, `jobs.py`, and API DTOs
- worker-to-core transport details live in `ml_core.py`
- worker diagnostics and control-plane state live in `system.py` and `diagnostics.py`

Used by:

- API
- worker
- adapters
- frontend type mirrors
