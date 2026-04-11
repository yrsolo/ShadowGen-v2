from shadowgen_pipeline import PipelineContext, PipelineOutput

from .base import build_stub_output


class LegacyStubAdapter:
    def render(self, context: PipelineContext) -> PipelineOutput:
        _ = context
        return build_stub_output(["Legacy black-box adapter is not connected yet."])
