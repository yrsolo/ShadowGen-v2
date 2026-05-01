from dataclasses import dataclass, field

from shadowgen_contracts import ErrorInfo

from .context import PipelineOutput


@dataclass(slots=True)
class PipelineCapabilitiesSummary:
    mode: str
    async_enabled: bool
    execution_default_backend: str | None = None
    refreshed_at_iso: str | None = None
    degraded: bool = False
    notes: list[str] = field(default_factory=list)
    components: list[dict[str, object]] = field(default_factory=list)


@dataclass(slots=True)
class PipelineSubmission:
    mode: str
    status: str
    core_job_id: str | None = None
    request_id: str | None = None
    result: PipelineOutput | None = None


@dataclass(slots=True)
class PipelinePollResult:
    status: str
    result: PipelineOutput | None = None
    error: ErrorInfo | None = None
    retryable: bool = False
