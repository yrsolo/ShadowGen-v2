# Repository Structure

This document describes the active structure that matters for runtime and maintenance.

## Top-Level Layout

### `apps/`

- `api` - FastAPI application and API composition
- `web` - Next.js application
- `worker` - background worker and worker control plane

### `packages/`

- `contracts` - shared DTOs and enums
- `application` - use cases and ports
- `domain` - entities, statuses, exceptions, value objects
- `pipeline` - pipeline context and interfaces
- `adapters` - infrastructure and ML adapters
- `schema` - placeholder for future schema artifacts

### `docs/`

Permanent documentation:

- `overview/` for fast orientation
- `reference/` for detailed module docs
- `architecture/` for boundaries and design
- `contracts/` for request/response shapes
- `roadmap/` for migration notes

### `scripts/`

Operational scripts for local bootstrap, docs checks, local container runs, and deployment helpers.

### `tests/`

- `unit/`
- `integration/`
- `smoke/`

## Runtime Entry Points

Active runtime entrypoints:

- API app: `apps/api/src/shadowgen_api/main.py`
- Worker app: `apps/worker/src/shadowgen_worker/main.py`
- Web app: `apps/web/src/app/page.tsx`

## Important Note About Older Bootstrap Leftovers

Some app folders still contain earlier bootstrap scaffolding under `apps/api/src/` outside `shadowgen_api`. These are not the primary runtime entrypoints and should not be treated as the current architecture source of truth.
