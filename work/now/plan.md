# Plan

## Steps

1. Compare the three worker container scripts and choose the stable single behavior.
2. Update `scripts/run-worker-cloud-container.cmd` to be the detached restart-policy launcher.
3. Delete the detached and self-managed variants.
4. Replace all docs and env-example references with the single script.
5. Run docs checks and a text search for stale script names.

## Checks

- `powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1`
- `rg -n "run-worker-cloud-container-detached|run-worker-cloud-container-self-managed|self-managed" README.md docs scripts .env.shadowgen.example`
