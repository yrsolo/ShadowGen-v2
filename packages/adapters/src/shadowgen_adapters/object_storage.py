from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.client import BaseClient


def build_s3_client(
    endpoint_url: str,
    bucket_region: str,
    access_key_id: str,
    secret_access_key: str,
) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=bucket_region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )


def normalize_storage_prefix(prefix: str | None) -> str:
    return prefix.strip("/ ") if prefix else "shadowgen-v2"


def prefixed_key(prefix: str, path: str) -> str:
    clean_prefix = normalize_storage_prefix(prefix)
    clean_path = path.lstrip("/")
    return f"{clean_prefix}/{clean_path}" if clean_prefix else clean_path


def dump_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")

