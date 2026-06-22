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

    def delete(self, job: JobRecord) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._job_key(job.job_id))
        if job.request_cache_key:
            indexed = self._get_indexed(job.request_cache_key)
            if indexed is not None and indexed.job_id == job.job_id:
                self.client.delete_object(Bucket=self.bucket, Key=self._request_cache_index_key(job.request_cache_key))

    def clear_request_cache(self) -> int:
        cleared = 0
        for key in self._list_keys(prefixed_key(self.prefix, "jobs/")):
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            job = JobRecord.model_validate(json.loads(response["Body"].read().decode("utf-8")))
            if not job.request_cache_key and not job.cache_status and not job.reused_existing_job:
                continue
            if job.request_cache_key:
                cleared += 1
            job.request_cache_key = None
            job.cache_status = None
            job.reused_existing_job = False
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=dump_json_bytes(job.model_dump(mode="json")),
                ContentType="application/json",
            )
        for key in self._list_keys(prefixed_key(self.prefix, "jobs-cache/")):
            self.client.delete_object(Bucket=self.bucket, Key=key)
            cleared += 1
        return cleared

    def find_by_request_cache_key(self, cache_key: str) -> JobRecord | None:
        return self._get_indexed(cache_key)

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
        if job.request_cache_key:
            self.client.put_object(
                Bucket=self.bucket,
                Key=self._request_cache_index_key(job.request_cache_key),
                Body=dump_json_bytes({"job_id": job.job_id}),
                ContentType="application/json",
            )

    def _job_key(self, job_id: str) -> str:
        return prefixed_key(self.prefix, f"jobs/{job_id}.json")

    def _request_cache_index_key(self, cache_key: str) -> str:
        return prefixed_key(self.prefix, f"jobs-cache/{cache_key}.json")

    def _list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        continuation_token = None
        while True:
            kwargs = {"Bucket": self.bucket, "Prefix": prefix}
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token
            response = self.client.list_objects_v2(**kwargs)
            keys.extend(item["Key"] for item in response.get("Contents", []))
            if not response.get("IsTruncated"):
                return keys
            continuation_token = response.get("NextContinuationToken")
            if not continuation_token:
                return keys

    def _get_indexed(self, cache_key: str) -> JobRecord | None:
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=self._request_cache_index_key(cache_key),
            )
        except self.client.exceptions.NoSuchKey:
            return None
        payload = json.loads(response["Body"].read().decode("utf-8"))
        job_id = payload.get("job_id")
        if not job_id:
            return None
        job = self.get(job_id)
        if job is None or job.request_cache_key != cache_key:
            return None
        return job
