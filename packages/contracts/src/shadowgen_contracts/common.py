from pydantic import BaseModel

from .enums import AssetKind


class AssetRef(BaseModel):
    asset_id: str
    kind: AssetKind
    mime_type: str
    url: str | None = None


class ProcessingMetrics(BaseModel):
    total_ms: int = 0
    decode_ms: int | None = None
    geometry_ms: int | None = None
    detection_ms: int | None = None
    segmentation_ms: int | None = None
    foreground_refinement_ms: int | None = None
    depth_ms: int | None = None
    normals_ms: int | None = None
    shadow_ms: int | None = None
    composition_ms: int | None = None
    encode_ms: int | None = None
    cache_ms: int | None = None


__all__ = ["AssetRef", "ProcessingMetrics"]
