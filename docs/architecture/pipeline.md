# Pipeline Architecture

At the first stage the pipeline is treated as a single black-box process wrapped behind a stable interface.

## Current Model

```text
Worker -> RenderPipeline -> MLCorePipelineAdapter -> New ML Service
                         \\-> LegacyHttpAdapter -> Old ShadowGEN server
```

## Why This Layer Exists

The new system should depend on a stable processing interface, not on direct imports from the old ML implementation.

## Current Adapter Split

- `MLCorePipelineAdapter` probes `/health` and `/v1/capabilities`, then selects sync `/v1/render` or async `/v1/render/jobs`
- `LegacyHttpAdapter` is selected only when ML-core handshake is unavailable and `/test` returns 2xx
- `MLCoreStubAdapter` provides deterministic local behavior when no remote URL is configured

The adapter forwards `shadow.model` unchanged, including `v1-gan` and `v2-diff`. It always sends the ML-core contract version `pipeline_version="ml-shadowgen-v1"` to the new service; the public job DTO's legacy pipeline field is not used to select the ML-core transport contract. For async calls it uses the durable business job id as `request_id`, matching ML-service idempotency semantics.

Diagnostics stay on the worker side. Submit failures record the ML HTTP method, endpoint, status, error code, and message on the `ml_submit` stage. Async terminal failures record ML job id, request id, status, and error payload on the `ml_poll` stage. The public API reads these persisted traces from shared state instead of probing the private ML service directly.

## Evolution Path

Later the pipeline may be split into stages:

1. description or detection
2. segmentation
3. normalization
4. shadow generation
5. composition
6. export

That split is intentionally deferred until the new architecture around jobs and contracts is stable.
