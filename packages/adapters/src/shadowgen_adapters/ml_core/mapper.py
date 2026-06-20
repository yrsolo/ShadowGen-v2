from __future__ import annotations

import base64

from shadowgen_contracts import (
    AssetKind,
    ErrorInfo,
    MLCoreBackgroundSpec,
    MLCoreOutputSpec,
    MLCorePreprocessSpec,
    MLCoreRenderRequest,
    MLCoreRenderResponse,
    MLCoreShadowSpec,
    ProcessingMetrics,
    MLCoreSourcePayload,
    RenderRequest,
)
from shadowgen_pipeline import PipelineArtifact, PipelineOutput


ML_CORE_PIPELINE_VERSION = "ml-shadowgen-v1"


def map_business_request_to_ml_core_request(
    request: RenderRequest,
    source_bytes: bytes,
    source_mime_type: str,
    request_id: str | None = None,
) -> MLCoreRenderRequest:
    return MLCoreRenderRequest(
        request_id=request_id,
        pipeline_version=ML_CORE_PIPELINE_VERSION,
        source=MLCoreSourcePayload(
            mime_type=source_mime_type,
            image_base64=base64.b64encode(source_bytes).decode("ascii"),
        ),
        preprocess=MLCorePreprocessSpec(padding_px=request.preprocess.padding_px),
        shadow=MLCoreShadowSpec(
            model=request.shadow.model,
            angle_deg=request.shadow.angle_deg,
            elevation_deg=request.shadow.elevation_deg,
            softness=request.shadow.softness,
            opacity=request.shadow.opacity,
            reflection=request.shadow.reflection,
        ),
        background=MLCoreBackgroundSpec(
            mode=request.background.mode.value,
            color_hex=request.background.color_hex,
        ),
        output=MLCoreOutputSpec(
            format=request.output.format.value,
            width=request.output.width,
            height=request.output.height,
            return_debug=request.output.return_debug,
        ),
    )


def map_ml_core_response_to_pipeline_output(response: MLCoreRenderResponse) -> PipelineOutput:
    artifacts: list[PipelineArtifact] = []
    for artifact in response.artifacts:
        kind = AssetKind.DEBUG if artifact.kind == "debug" else AssetKind.FINAL
        artifacts.append(
            PipelineArtifact(
                kind=kind,
                mime_type=artifact.mime_type,
                data=base64.b64decode(artifact.image_base64),
            )
        )
    return PipelineOutput(
        artifacts=artifacts,
        metrics=ProcessingMetrics.model_validate(response.metrics.model_dump()),
        warnings=response.warnings,
    )


def map_ml_core_error_payload(payload: dict) -> ErrorInfo:
    error_payload = payload.get("error") or {}
    details = error_payload.get("details")
    if error_payload.get("request_id") and isinstance(details, dict):
        details = {**details, "request_id": error_payload.get("request_id")}
    elif error_payload.get("request_id"):
        details = {"request_id": error_payload.get("request_id")}
    return ErrorInfo(
        code=error_payload.get("code", "processing_failed"),
        message=error_payload.get("message", "ML core request failed."),
        details=details,
    )
