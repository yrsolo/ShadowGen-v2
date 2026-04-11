# Contracts Package

Path:

- `packages/contracts/src/shadowgen_contracts`

Purpose:

- define shared DTOs, enums, diagnostics models, job contracts, render contracts, and worker-system contracts

Key files:

- `render.py` - render request/result DTOs
- `jobs.py` - job DTOs and queue message
- `assets.py` - asset refs
- `diagnostics.py` - diagnostics payloads
- `system.py` - runtime config and worker action contracts
- `errors.py` - shared error models
- `enums.py` - shared enums

Used by:

- API
- worker
- adapters
- frontend type mirrors
