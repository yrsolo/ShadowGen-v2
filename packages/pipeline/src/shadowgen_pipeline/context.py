from dataclasses import dataclass

from shadowgen_contracts import AssetKind, ProcessingMetrics, RenderRequest


@dataclass(slots=True)
class PipelineContext:
    request: RenderRequest
    source_image: bytes
    source_mime_type: str
    request_id: str | None = None


@dataclass(slots=True)
class PipelineArtifact:
    kind: AssetKind
    mime_type: str
    data: bytes


@dataclass(slots=True)
class PipelineOutput:
    artifacts: list[PipelineArtifact]
    metrics: ProcessingMetrics
    warnings: list[str]
