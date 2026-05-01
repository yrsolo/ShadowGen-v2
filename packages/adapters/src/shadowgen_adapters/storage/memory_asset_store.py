import hashlib

from shadowgen_contracts import AssetKind, AssetRef
from shadowgen_domain import AssetNotFoundError


class InMemoryAssetStore:
    def __init__(self) -> None:
        self._bytes: dict[str, bytes] = {}
        self._refs: dict[str, AssetRef] = {}
        self._hashes: dict[str, str] = {}
        self._seq = 0

    def put_bytes(self, data: bytes, kind: AssetKind, mime_type: str) -> AssetRef:
        self._seq += 1
        asset_id = f"{kind.value}-{self._seq}"
        ref = AssetRef(asset_id=asset_id, kind=kind, mime_type=mime_type, url=None)
        self._bytes[asset_id] = data
        self._refs[asset_id] = ref
        self._hashes[asset_id] = hashlib.sha256(data).hexdigest()
        return ref

    def get_bytes(self, asset_id: str) -> bytes:
        return self._bytes[asset_id]

    def get_ref(self, asset_id: str) -> AssetRef | None:
        return self._refs.get(asset_id)

    def get_source_hash(self, asset_id: str) -> str:
        source_hash = self._hashes.get(asset_id)
        if source_hash is None:
            raise AssetNotFoundError(f"Asset '{asset_id}' was not found.")
        return source_hash

    def clear(self) -> None:
        self._bytes.clear()
        self._refs.clear()
        self._hashes.clear()
        self._seq = 0
