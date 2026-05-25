# Current Task

## Task

Consolidate worker container launch scripts.

## Goal

Keep one clear worker-container entrypoint instead of three similar scripts:

1. keep `scripts/run-worker-cloud-container.cmd`
2. make it the stable detached always-on mode
3. remove the detached and self-managed variants
4. update docs and tracking so operator instructions point to the single script

## Scope Of This Stage

- merge detached restart-policy behavior into `run-worker-cloud-container.cmd`
- remove obsolete worker container script variants
- update README, overview, reference docs, and env comments
- run docs/link checks

## Risks

- stale docs may still point to removed scripts
- losing the foreground mode is intentional, but logs must remain discoverable through `docker logs -f shadowgen-worker`
