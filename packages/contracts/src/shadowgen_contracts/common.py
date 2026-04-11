from pydantic import BaseModel

from .enums import AssetKind


class AssetRef(BaseModel):
    asset_id: str
    kind: AssetKind
    mime_type: str
    url: str | None = None


class ProcessingMetrics(BaseModel):
    total_ms: int = 0


__all__ = ["AssetRef", "ProcessingMetrics"]
