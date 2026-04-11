from __future__ import annotations

import json

from botocore.client import BaseClient

from shadowgen_adapters.object_storage import dump_json_bytes, prefixed_key
from shadowgen_contracts import JobRecord


class S3JobRepository:
    def __init__(self, client: BaseClient, bucket: str, prefix: str) -> None:
        self.client = client
        self.bucket = bucket
        self.prefix = prefix

    def create(self, job: JobRecord) -> None:
        self._write(job)

    def get(self, job_id: str) -> JobRecord | None:
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=self._job_key(job_id),
            )
        except self.client.exceptions.NoSuchKey:
            return None
        return JobRecord.model_validate(json.loads(response["Body"].read().decode("utf-8")))

    def update(self, job: JobRecord) -> None:
        self._write(job)

    def list_recent(self, limit: int = 20) -> list[JobRecord]:
        prefix = prefixed_key(self.prefix, "jobs/")
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        records = []
        for item in contents:
            response_item = self.client.get_object(Bucket=self.bucket, Key=item["Key"])
            records.append(JobRecord.model_validate(json.loads(response_item["Body"].read().decode("utf-8"))))
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records[:limit]

    def _write(self, job: JobRecord) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._job_key(job.job_id),
            Body=dump_json_bytes(job.model_dump(mode="json")),
            ContentType="application/json",
        )

    def _job_key(self, job_id: str) -> str:
        return prefixed_key(self.prefix, f"jobs/{job_id}.json")

