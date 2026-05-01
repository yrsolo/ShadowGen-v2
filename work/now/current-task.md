# Current Task

## Task

Improve diagnostics, request handling, runtime rollout, worker container stability, and frontend model selection in connected places:

1. make worker `Recent Jobs` readable and useful with a human-friendly completion timestamp and a small result preview
2. short-circuit duplicate render submissions so identical image bytes with identical render parameters reuse an existing job instead of enqueueing a duplicate
3. deploy the refreshed containers so the new behavior is visible in the live worker UI and cloud runtime
4. remove obvious cache-hit latency in the API path so duplicate requests are served close to instantly
5. make the local worker container self-contained by default instead of bind-mounting the whole repository into Docker Desktop
6. support the updated ML-core frontend shadow-model contract with selectable `V1-GAN` and `V2-DIFF` modes
7. document how to move the worker to a new always-on Docker host and make the worker env template self-explanatory

## Goal

Update the worker local control UI so that:

1. each recent successful job shows date and time down to seconds without fractional seconds
2. a small preview is shown when the worker can fetch the final result image directly from its current asset store
3. missing or unavailable assets fail quietly and do not break the worker UI
4. the JSON status payload and tests stay aligned with the new fields

Update job creation so that:

5. the cache key is derived from source image bytes plus normalized render parameters
6. re-uploading the same binary image with the same render settings still hits the same request cache
7. matching `queued`, `running`, or `succeeded` jobs are returned immediately and never re-published to the queue
8. failed or canceled jobs remain retryable
9. cache-hit lookup avoids full source downloads and full job scans where the current storage backend can provide metadata and a direct cache index

Update worker container startup so that:

10. the normal worker container launch does not mount the repository
11. the normal worker container launch does not mount Docker socket
12. container self-management/update-from-git is explicitly opt-in instead of enabled by default
13. docs explain the tradeoff: stable portable container by default, self-managed dev mode only when the operator accepts Docker socket + repo mount risks

Update the product UI and worker/core contract so that:

14. `shadow.model` can be sent as `v1-gan` or `v2-diff`
15. `v1-gan` keeps manual angle control
16. `v2-diff` is shown as automatic and does not expose ineffective manual shadow controls in the basic UI
17. mobile layout defaults to a vertical, phone-friendly workflow
18. advanced mode keeps the previous manual controls and engineering/detail affordances available
19. the ML-core adapter sends `source.image_base64` according to the updated core contract
20. the minimal mobile interface follows the compact preview-first composition from `design/ref`
21. the top selector names the models `Top` and `Side`
22. the bottom selector switches between `Min`, `Max`, and `Engineering`
23. the source preview area itself becomes the entry point for upload and device-camera capture
24. a small close button clears the loaded source preview so another image can be selected quickly

## Scope Of This Stage

- update worker control-app payload building for recent jobs
- add safe preview extraction from the current asset store
- improve the worker dashboard HTML layout for recent jobs
- normalize render-request cache key generation so `source_asset_id` does not defeat deduplication
- teach job repositories to find existing jobs by request cache key
- short-circuit duplicate job creation before queue publish
- rebuild and redeploy the relevant containers after the UI/cache changes are verified
- update tracking, evidence, docs, and focused tests
- add an operator runbook for a permanent worker Docker host
- document the required `.env.shadowgen` values directly in the env template
- add a detached worker-container script for always-on Docker operation

## Risks

- bloating the worker dashboard payload with large inline previews
- breaking the local worker page when an old result asset is missing
- making the JSON payload inconsistent with the rendered HTML
- accidentally suppressing legitimate retries after failed jobs
- turning cache behavior into hidden magic if it is not documented clearly
- partial rollout where repo code is newer than the running worker or serverless containers
- Docker Desktop instability from large Windows/network bind mounts into the worker container
- accidentally keeping dangerous Docker socket access enabled in the normal worker path
- confusing users by showing controls that do not currently affect `v2-diff`
- drifting from the ML-core request schema while the new service is evolving
