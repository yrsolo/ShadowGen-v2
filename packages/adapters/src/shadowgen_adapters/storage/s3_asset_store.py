from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from botocore.client import BaseClient

from shadowgen_adapters.object_storage import dump_json_bytes, prefixed_key
from shadowgen_contracts import AssetKind, AssetRef
from shadowgen_domain import AssetNotFoundError


class S3AssetStore:
    def __init__(self, client: BaseClient, bucket: str, prefix: str) -> None:
        self.client = client
        self.bucket = bucket
        self.prefix = prefix

    def put_bytes(self, data: bytes, kind: AssetKind, mime_type: str) -> AssetRef:
        asset_id = f"{kind.value}-{uuid4()}"
        object_key = prefixed_key(self.prefix, f"assets/{kind.value}/{asset_id}")
        metadata_key = prefixed_key(self.prefix, f"assets/meta/{asset_id}.json")
        ref = AssetRef(asset_id=asset_id, kind=kind, mime_type=mime_type, url=None)

        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=mime_type,
        )
        self.client.put_object(
            Bucket=self.bucket,
            Key=metadata_key,
            Body=dump_json_bytes(
                {
                    "asset": ref.model_dump(mode="json"),
                    "object_key": object_key,
                    "source_hash": hashlib.sha256(data).hexdigest(),
                }
            ),
            ContentType="application/json",
        )
        return ref

    def get_bytes(self, asset_id: str) -> bytes:
        metadata = self._get_metadata(asset_id)
        response = self.client.get_object(Bucket=self.bucket, Key=metadata["object_key"])
        return response["Body"].read()

    def get_ref(self, asset_id: str) -> AssetRef | None:
        try:
            metadata = self._get_metadata(asset_id)
        except self.client.exceptions.NoSuchKey:
            return None
        return AssetRef.model_validate(metadata["asset"])

    def get_source_hash(self, asset_id: str) -> str:
        try:
            metadata = self._get_metadata(asset_id)
        except self.client.exceptions.NoSuchKey as exc:
            raise AssetNotFoundError(f"Asset '{asset_id}' was not found.") from exc
        source_hash = metadata.get("source_hash")
        if source_hash:
            return source_hash
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=metadata["object_key"])
        except self.client.exceptions.NoSuchKey as exc:
            raise AssetNotFoundError(f"Asset '{asset_id}' was not found.") from exc
        return hashlib.sha256(response["Body"].read()).hexdigest()

    def _get_metadata(self, asset_id: str) -> dict:
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=prefixed_key(self.prefix, f"assets/meta/{asset_id}.json"),
        )
        return json.loads(response["Body"].read().decode("utf-8"))
