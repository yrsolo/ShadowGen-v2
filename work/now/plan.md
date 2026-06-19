# Plan

## Steps

1. Align worker-side health/capabilities DTOs with the authoritative new service schema.
2. Tighten service detection so only a 2xx `/test` identifies legacy.
3. Select sync/async endpoints from capabilities and support current async status vocabulary.
4. Add tests using realistic new-service capability and job payloads plus legacy fallback tests.
5. Update integration docs and evidence.

## Checks

- `python -m pytest tests/unit/test_ml_core_adapter.py tests/unit/test_legacy_http_adapter.py`
- `python -m pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
