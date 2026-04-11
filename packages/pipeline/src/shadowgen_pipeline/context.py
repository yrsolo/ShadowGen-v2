from dataclasses import dataclass

from shadowgen_contracts import AssetKind, ProcessingMetrics, RenderRequest


@dataclass(slots=True)
class PipelineContext:
    request: RenderRequest
    source_image: bytes
    source_mime_type: str


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
