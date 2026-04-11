# Pipeline Package

Path:

- `packages/pipeline/src/shadowgen_pipeline`

Purpose:

- define the internal pipeline boundary between the worker and the ML adapter

Key files:

- `context.py` - `PipelineContext`, `PipelineArtifact`, `PipelineOutput`
- `interfaces.py` - `RenderPipeline` protocol
- `cache_keys.py` - request-derived cache helpers

Current model:

- worker builds `PipelineContext`
- adapter returns `PipelineOutput`
- the rest of the system does not depend on ML transport details
