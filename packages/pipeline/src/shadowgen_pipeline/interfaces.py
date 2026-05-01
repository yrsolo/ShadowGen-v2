from typing import Protocol

from .context import PipelineContext
from .execution import PipelineCapabilitiesSummary, PipelinePollResult, PipelineSubmission


class RenderPipeline(Protocol):
    def probe(self, force_refresh: bool = False) -> PipelineCapabilitiesSummary:
        ...

    def submit(self, context: PipelineContext) -> PipelineSubmission:
        ...

    def poll(self, submission: PipelineSubmission) -> PipelinePollResult:
        ...

    def cancel(self, submission: PipelineSubmission) -> None:
        ...
