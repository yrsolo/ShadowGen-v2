from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from shadowgen_contracts import AssetKind, AssetRef
from shadowgen_domain import AssetNotFoundError


class FileAssetStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.bytes_dir = self.root_dir / "bytes"
        self.meta_dir = self.root_dir / "meta"
        self.bytes_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, data: bytes, kind: AssetKind, mime_type: str) -> AssetRef:
        asset_id = f"{kind.value}-{uuid4()}"
        ref = AssetRef(asset_id=asset_id, kind=kind, mime_type=mime_type, url=None)
        (self.bytes_dir / asset_id).write_bytes(data)
        (self.meta_dir / f"{asset_id}.json").write_text(
            json.dumps(
                {
                    "asset": ref.model_dump(mode="json"),
                    "source_hash": hashlib.sha256(data).hexdigest(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return ref

    def get_bytes(self, asset_id: str) -> bytes:
        return (self.bytes_dir / asset_id).read_bytes()

    def get_ref(self, asset_id: str) -> AssetRef | None:
        path = self.meta_dir / f"{asset_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "asset" in payload:
            return AssetRef.model_validate(payload["asset"])
        return AssetRef.model_validate(payload)

    def get_source_hash(self, asset_id: str) -> str:
        path = self.meta_dir / f"{asset_id}.json"
        if not path.exists():
            raise AssetNotFoundError(f"Asset '{asset_id}' was not found.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_hash = payload.get("source_hash")
        if source_hash:
            return source_hash
        bytes_path = self.bytes_dir / asset_id
        if not bytes_path.exists():
            raise AssetNotFoundError(f"Asset '{asset_id}' was not found.")
        return hashlib.sha256(bytes_path.read_bytes()).hexdigest()
