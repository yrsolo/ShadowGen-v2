from __future__ import annotations

import json

from botocore.client import BaseClient

from shadowgen_adapters.object_storage import dump_json_bytes, prefixed_key
from shadowgen_contracts import LocalRuntimeConfig


class S3RuntimeConfigStore:
    def __init__(self, client: BaseClient, bucket: str, prefix: str) -> None:
        self.client = client
        self.bucket = bucket
        self.prefix = prefix

    def get(self) -> LocalRuntimeConfig:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self._key)
        except self.client.exceptions.NoSuchKey:
            return LocalRuntimeConfig()
        return LocalRuntimeConfig.model_validate(json.loads(response["Body"].read().decode("utf-8")))

    def update(self, config: LocalRuntimeConfig) -> LocalRuntimeConfig:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key,
            Body=dump_json_bytes(config.model_dump(mode="json")),
            ContentType="application/json",
        )
        return config

    @property
    def _key(self) -> str:
        return prefixed_key(self.prefix, "runtime/config.json")

