from typing import Protocol

from .context import PipelineContext, PipelineOutput


class RenderPipeline(Protocol):
    def render(self, context: PipelineContext) -> PipelineOutput:
        ...
