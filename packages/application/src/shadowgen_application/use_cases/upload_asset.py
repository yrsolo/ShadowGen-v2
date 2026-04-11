from shadowgen_application.ports import AssetStorePort
from shadowgen_contracts import AssetKind, AssetRef


class UploadAssetUseCase:
    def __init__(self, asset_store: AssetStorePort) -> None:
        self.asset_store = asset_store

    def execute(self, data: bytes, mime_type: str) -> AssetRef:
        return self.asset_store.put_bytes(data=data, kind=AssetKind.SOURCE, mime_type=mime_type)
