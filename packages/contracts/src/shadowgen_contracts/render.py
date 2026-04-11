from pydantic import BaseModel, Field

from .common import AssetRef, ProcessingMetrics
from .enums import BackgroundMode, OutputFormat


class ShadowSettings(BaseModel):
    angle_deg: float = Field(default=45.0, ge=0.0, le=360.0)
    elevation_deg: float = Field(default=45.0, ge=0.0, le=90.0)
    softness: float = Field(default=0.5, ge=0.0, le=1.0)
    opacity: float = Field(default=0.6, ge=0.0, le=1.0)
    reflection: float = Field(default=0.0, ge=0.0, le=1.0)


class BackgroundSpec(BaseModel):
    mode: BackgroundMode = BackgroundMode.SOLID
    color_hex: str = "#FFFFFF"


class OutputSpec(BaseModel):
    format: OutputFormat = OutputFormat.PNG
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    return_debug: bool = False


class RenderRequest(BaseModel):
    source_asset_id: str
    pipeline_version: str = "legacy-black-box-v1"
    shadow: ShadowSettings = ShadowSettings()
    background: BackgroundSpec = BackgroundSpec()
    output: OutputSpec = OutputSpec()


class RenderResult(BaseModel):
    images: list[AssetRef]
    debug_images: list[AssetRef] = []
    metrics: ProcessingMetrics = ProcessingMetrics()
    warnings: list[str] = []


__all__ = [
    "BackgroundSpec",
    "OutputSpec",
    "RenderRequest",
    "RenderResult",
    "ShadowSettings",
]
