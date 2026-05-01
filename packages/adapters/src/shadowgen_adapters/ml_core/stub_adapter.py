from __future__ import annotations

from datetime import datetime, timezone

from shadowgen_contracts import ErrorInfo
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelineContext, PipelinePollResult, PipelineSubmission

from shadowgen_adapters.legacy_pipeline.base import build_stub_output


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MLCoreStubAdapter:
    def probe(self, force_refresh: bool = False) -> PipelineCapabilitiesSummary:
        _ = force_refresh
        return PipelineCapabilitiesSummary(
            mode="sync",
            async_enabled=False,
            execution_default_backend="stub",
            refreshed_at_iso=utc_now_iso(),
            degraded=False,
            notes=["Stub ML core adapter is active."],
        )

    def submit(self, context: PipelineContext) -> PipelineSubmission:
        _ = context
        return PipelineSubmission(
            mode="sync",
            status="succeeded",
            result=build_stub_output(["ML core stub adapter is active."]),
        )

    def poll(self, submission: PipelineSubmission) -> PipelinePollResult:
        if submission.result is not None:
            return PipelinePollResult(status="succeeded", result=submission.result)
        return PipelinePollResult(
            status="failed",
            error=ErrorInfo(code="processing_failed", message="Stub adapter returned no result."),
            retryable=False,
        )

    def cancel(self, submission: PipelineSubmission) -> None:
        _ = submission
