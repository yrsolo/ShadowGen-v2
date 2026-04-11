from pydantic import BaseModel

from .common import AssetRef


class CreateAssetResponse(BaseModel):
    asset: AssetRef


class GetAssetResponse(BaseModel):
    asset: AssetRef


__all__ = ["CreateAssetResponse", "GetAssetResponse"]
