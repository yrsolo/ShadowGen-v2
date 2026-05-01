from shadowgen_contracts import ErrorInfo
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelineContext, PipelinePollResult, PipelineSubmission

from .base import build_stub_output


class LegacyStubAdapter:
    def probe(self, force_refresh: bool = False) -> PipelineCapabilitiesSummary:
        _ = force_refresh
        return PipelineCapabilitiesSummary(
            mode="legacy-sync",
            async_enabled=False,
            execution_default_backend="legacy-stub",
            notes=["Legacy stub adapter is active."],
        )

    def submit(self, context: PipelineContext) -> PipelineSubmission:
        _ = context
        return PipelineSubmission(
            mode="sync",
            status="succeeded",
            result=build_stub_output(["Legacy black-box adapter is not connected yet."]),
        )

    def poll(self, submission: PipelineSubmission) -> PipelinePollResult:
        if submission.result is not None:
            return PipelinePollResult(status="succeeded", result=submission.result)
        return PipelinePollResult(
            status="failed",
            error=ErrorInfo(code="processing_failed", message="Legacy stub adapter returned no result."),
            retryable=False,
        )

    def cancel(self, submission: PipelineSubmission) -> None:
        _ = submission
