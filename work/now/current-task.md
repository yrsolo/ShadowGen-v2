# Current Task

## Task

Implement clearer operational diagnostics for jobs, worker liveness, and ML availability.

## Goal

Make failures and stalls diagnosable from the engineering UI and local worker control page by:

1. storing a compact per-job trace with processing stages and durations
2. surfacing cache-hit/reuse status when creating jobs
3. adding an explicit worker `diagnostic_probe` action round-trip
4. publishing worker-side ML probe status without making the API call ML directly
5. showing job dates, micro previews, copyable job ids, and expandable timelines
6. using a five-minute stale threshold for worker life indicators

## Scope Of This Stage

- extend job and worker diagnostic contracts
- add trace updates in create-job and process-job orchestration
- add worker-side diagnostic probe action using existing ML health/test compatibility
- update web engineering panel and worker control UI diagnostics
- update targeted tests, docs, and evidence

## Risks

- older persisted jobs will not have trace data and must render gracefully
- diagnostic probe must not expose direct public access to the private worker
- trace must stay compact and avoid embedding image or large ML payload data
