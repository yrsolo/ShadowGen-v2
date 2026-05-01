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

## Duplicate Request Reuse

Job creation now performs request-level deduplication before publishing to the queue.

Cache key inputs:

- source image bytes hash
- normalized render request payload

Normalization rule:

- `source_asset_id` is ignored for the cache key so the same binary image with the same render parameters can reuse an existing job even if it was re-uploaded as a different asset ID

Reuse behavior:

- if a matching job is already `queued`, `running`, or `succeeded`, API returns that existing job instead of creating a new one
- only `failed` or `canceled` jobs are eligible for a fresh retry with the same parameters

Performance note:

- the source hash is read from asset metadata when available, so cache-hit lookup does not need to download the full source image again
- file and S3 repositories maintain a direct request-cache index so cache-hit lookup does not need to scan all stored jobs
- S3/Object Storage request-cache lookup is index-only: a missing cache-index object is treated as a cache miss, and the API does not scan `jobs/*.json` on the `POST /v1/jobs` hot path
