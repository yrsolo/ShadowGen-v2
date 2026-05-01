from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MLCoreHealthResponse(BaseModel):
    status: str
    async_enabled: bool = False


class MLCoreBackendCapability(BaseModel):
    kind: str
    available: bool = True
    supports_batching: bool = False
    supports_async: bool = False
    model_variant: str | None = None
    fallback_reason: str | None = None


class MLCoreComponentCapability(BaseModel):
    name: str
    available: bool = True
    backend_kind: str | None = None
    model_variant: str | None = None
    supports_batching: bool = False
    supports_async: bool = False
    fallback_reason: str | None = None
    backends: list[MLCoreBackendCapability] = []


class MLCoreCapabilitiesResponse(BaseModel):
    execution_default_backend: str | None = None
    async_enabled: bool = False
    components: list[MLCoreComponentCapability] = []


class MLCoreSourcePayload(BaseModel):
    mime_type: str
    image_base64: str


class MLCorePreprocessSpec(BaseModel):
    padding_px: int = Field(default=100, ge=0)


class MLCoreShadowSpec(BaseModel):
    model: Literal["v1-gan", "v2-diff"] = "v1-gan"
    angle_deg: float = Field(default=45.0, ge=0.0, le=360.0)
    elevation_deg: float = Field(default=45.0, ge=0.0, le=90.0)
    softness: float = Field(default=0.5, ge=0.0, le=1.0)
    opacity: float = Field(default=0.6, ge=0.0, le=1.0)
    reflection: float = Field(default=0.0, ge=0.0, le=1.0)


class MLCoreBackgroundSpec(BaseModel):
    mode: str = "solid"
    color_hex: str = "#FFFFFF"


class MLCoreOutputSpec(BaseModel):
    format: str = "png"
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    return_debug: bool = False


class MLCoreRenderRequest(BaseModel):
    request_id: str | None = None
    pipeline_version: str = "ml-shadowgen-v1"
    source: MLCoreSourcePayload
    preprocess: MLCorePreprocessSpec = MLCorePreprocessSpec()
    shadow: MLCoreShadowSpec = MLCoreShadowSpec()
    background: MLCoreBackgroundSpec = MLCoreBackgroundSpec()
    output: MLCoreOutputSpec = MLCoreOutputSpec()


class MLCoreArtifact(BaseModel):
    name: str = "final"
    kind: str = "final"
    mime_type: str = "image/png"
    image_base64: str


class MLCoreMetrics(BaseModel):
    total_ms: int = 0
    decode_ms: int | None = None
    segmentation_ms: int | None = None
    shadow_ms: int | None = None
    composition_ms: int | None = None
    encode_ms: int | None = None


class MLCoreModelInfo(BaseModel):
    service_version: str | None = None
    model_version: str | None = None
    build_id: str | None = None
    weights_hash: str | None = None


class MLCoreErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, str] | None = None
    request_id: str | None = None


class MLCoreRenderResponse(BaseModel):
    request_id: str | None = None
    artifacts: list[MLCoreArtifact] = []
    metrics: MLCoreMetrics = MLCoreMetrics()
    warnings: list[str] = []
    model_info: MLCoreModelInfo = MLCoreModelInfo()


class MLCoreAsyncSubmitResponse(BaseModel):
    job_id: str
    request_id: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MLCoreAsyncJobResponse(BaseModel):
    job_id: str
    request_id: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error: MLCoreErrorBody | None = None
    result: MLCoreRenderResponse | None = None
