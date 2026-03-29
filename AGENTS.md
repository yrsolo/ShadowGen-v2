# AGENTS.md

This file defines the required workflow for noticeable work in this repository.

## 1. Core Rule

Do not work chaotically. Significant changes should leave a visible trace in docs, tracking, tests, or runtime structure.

## 2. Before Starting

Before implementation, the agent must:

1. Read `README.md`
2. Read `docs/README.md`
3. Read `agent/OPERATING_CONTRACT.md`
4. Check `work/now/current-task.md`
5. Update `work/now/plan.md` if the task is larger than a tiny local edit

## 3. Source Of Truth

Documentation is not automatically the truth. Verify important claims against:

- code
- config
- tests
- runtime entrypoints
- CI scripts

## 4. Documentation Rules

Keep documentation layered:

- root `README.md` for overview
- `docs/overview/` for fast orientation
- `docs/architecture/` and `docs/reference/` for details
- `work/` for temporary working notes

## 5. Tracking

If the task is larger than a tiny edit:

- update `work/now/current-task.md`
- update `work/now/plan.md` when useful
- record results in `work/now/evidence.md`

## 6. Anti-Chaos Constraints

Do not create files without purpose. Do not duplicate documentation. Do not hide behavior in config or runtime side effects.

## 7. Before Finishing

The agent should:

1. Update touched docs
2. Run relevant checks
3. Update evidence
4. Suggest a deeper doc audit only after a larger milestone
