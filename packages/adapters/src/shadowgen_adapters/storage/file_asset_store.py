from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from shadowgen_contracts import AssetKind, AssetRef


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
        (self.meta_dir / f"{asset_id}.json").write_text(ref.model_dump_json(indent=2), encoding="utf-8")
        return ref

    def get_bytes(self, asset_id: str) -> bytes:
        return (self.bytes_dir / asset_id).read_bytes()

    def get_ref(self, asset_id: str) -> AssetRef | None:
        path = self.meta_dir / f"{asset_id}.json"
        if not path.exists():
            return None
        return AssetRef.model_validate(json.loads(path.read_text(encoding="utf-8")))
