# Pipeline Architecture

At the first stage the pipeline is treated as a single black-box process wrapped behind a stable interface.

## Current Model

Worker -> RenderPipeline -> LegacyPipelineAdapter -> Old ML Core

## Why This Layer Exists

The new system should depend on a stable processing interface, not on direct imports from the old ML implementation.

## Current Adapter Split

- `LegacyStubAdapter` for deterministic local tests
- `LegacyHttpAdapter` for optional live integration with the old ML server
- `LegacyPipelineAdapter` as a small facade selected by runtime config

## Evolution Path

Later the pipeline may be split into stages:

1. description or detection
2. segmentation
3. normalization
4. shadow generation
5. composition
6. export

That split is intentionally deferred until the new architecture around jobs and contracts is stable.
