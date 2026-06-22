# Job Model

## Statuses

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

## Required Fields

- `job_id`
- `status`
- `created_at`
- `updated_at`
- `request`

## Optional Fields

- `started_at`
- `finished_at`
- `error`
- `result`
- `request_cache_key`
- `trace`
- `cache_status`
- `reused_existing_job`

## Diagnostic Trace

`JobRecord.trace` is a compact timeline for engineering diagnostics. It stores small metadata only, never image bytes or large ML payloads.

Stage fields:

- `name`
- `status` - `running`, `succeeded`, `failed`, or `skipped`
- `started_at`
- `finished_at`
- `duration_ms`
- `message`
- `error`

Common stages:

- `created`
- `cache_lookup`
- `queued`
- `worker_claimed`
- `asset_ref_loaded`
- `asset_bytes_loaded`
- `ml_probe`
- `ml_submit`
- `ml_poll`
- `artifact_store`
- `completed`
- `failed`
- `terminal_noop`
- `operator_mark_failed`

## Lost Job Cleanup

Engineering diagnostics can classify stale live jobs as lost when metadata says `queued` or `running` but worker and queue state do not show matching active work.

Operator cleanup endpoints:

- `POST /v1/jobs/{job_id}/mark-failed` records the job as failed with an operator reason.
- `DELETE /v1/jobs/{job_id}` removes the job metadata and its request-cache index entry when it points at that job.
- `POST /v1/jobs/cache/clear` removes request-cache keys from job metadata and deletes cache index entries without deleting jobs or artifacts.

## Duplicate Request Reuse

Job creation now performs request-level deduplication before publishing to the queue.

Cache key inputs:

- source image bytes hash
- normalized render request payload

Normalization rule:

- `source_asset_id` is ignored for the cache key so the same binary image with the same render parameters can reuse an existing job even if it was re-uploaded as a different asset ID

Reuse behavior:

- if a matching job is already `queued`, `running`, or `succeeded`, API returns that existing job instead of creating a new one
- create-job responses include `cache_status` and `reused_existing_job` so the UI can distinguish a reused job from a newly queued one
- `queued` and `running` cache records are reused only while they are fresh; stale live records are ignored so a lost old job cannot trap new submissions forever
- only `failed` or `canceled` jobs are eligible for a fresh retry with the same parameters

Performance note:

- the source hash is read from asset metadata when available, so cache-hit lookup does not need to download the full source image again
- file and S3 repositories maintain a direct request-cache index so cache-hit lookup does not need to scan all stored jobs
- S3/Object Storage request-cache lookup is index-only: a missing cache-index object is treated as a cache miss, and the API does not scan `jobs/*.json` on the `POST /v1/jobs` hot path
