from __future__ import annotations

import base64

from shadowgen_contracts import AssetKind, ProcessingMetrics
from shadowgen_pipeline import PipelineArtifact, PipelineContext, PipelineOutput


_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def build_stub_output(warnings: list[str] | None = None) -> PipelineOutput:
    return PipelineOutput(
        artifacts=[
            PipelineArtifact(
                kind=AssetKind.FINAL,
                mime_type="image/png",
                data=_PLACEHOLDER_PNG,
            )
        ],
        metrics=ProcessingMetrics(total_ms=0),
        warnings=warnings or [],
    )
