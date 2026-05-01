# Pipeline Package

Path:

- `packages/pipeline/src/shadowgen_pipeline`

Purpose:

- define the internal pipeline boundary between the worker and the ML adapter

Key files:

- `context.py` - `PipelineContext`, `PipelineArtifact`, `PipelineOutput`
- `execution.py` - capabilities, submission, and poll result dataclasses
- `interfaces.py` - `RenderPipeline` protocol
- `cache_keys.py` - request-derived cache helpers

Current model:

- worker builds `PipelineContext`
- adapter exposes `probe`, `submit`, `poll`, and `cancel`
- sync path may return an inline result immediately
- async path returns a submission token and is completed through polling
- the rest of the system does not depend on ML transport details
