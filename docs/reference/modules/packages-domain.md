# Domain Package

Path:

- `packages/domain/src/shadowgen_domain`

Purpose:

- hold statuses, value objects, exceptions, and domain-level entities
- own job lifecycle invariants such as queued/running/terminal transitions

Key files:

- `entities.py`
- `statuses.py`
- `value_objects.py`
- `exceptions.py`

Design rule:

- no FastAPI, HTTP, queue, storage, or adapter knowledge
- no dependency on public API contract DTOs
