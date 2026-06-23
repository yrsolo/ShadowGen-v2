import io

from shadowgen_adapters.runtime.factories import build_runtime_adapters
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, LocalRuntimeConfig, RenderRequest, WorkerActionRecord, WorkerRuntimeState
from datetime import datetime, timezone
from shadowgen_pipeline.cache_keys import render_request_key


class FakeBody:
    def __init__(self, payload: bytes) -> None:
        self._buffer = io.BytesIO(payload)

    def read(self) -> bytes:
        return self._buffer.read()


class FakeS3Client:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict] = {}
        self.list_calls = 0
        self.get_calls_by_key: dict[str, int] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str | None = None):
        payload = Body if isinstance(Body, bytes) else Body.encode("utf-8")
        self.objects[(Bucket, Key)] = {"Body": payload, "ContentType": ContentType}
        return {"ETag": "fake"}

    def get_object(self, Bucket: str, Key: str):
        self.get_calls_by_key[Key] = self.get_calls_by_key.get(Key, 0) + 1
        item = self.objects.get((Bucket, Key))
        if item is None:
            raise self.exceptions.NoSuchKey(Key)
        return {"Body": FakeBody(item["Body"]), "ContentType": item.get("ContentType")}

    def delete_object(self, Bucket: str, Key: str):
        self.objects.pop((Bucket, Key), None)
        return {}

    def list_objects_v2(self, Bucket: str, Prefix: str):
        self.list_calls += 1
        contents = [{"Key": key} for current_bucket, key in self.objects if current_bucket == Bucket and key.startswith(Prefix)]
        return {"Contents": contents, "IsTruncated": False}


def test_s3_backed_runtime_supports_shared_state(monkeypatch) -> None:
    fake_client = FakeS3Client()

    monkeypatch.setattr(
        "shadowgen_adapters.runtime.factories.build_s3_client",
        lambda endpoint_url, bucket_region, access_key_id, secret_access_key: fake_client,
    )

    api_runtime = build_runtime_adapters(
        state_backend="s3",
        queue_backend="memory",
        state_dir=".shadowgen-ignored",
        s3_endpoint_url="https://storage.example.test",
        s3_bucket="shadowgen-bucket",
        s3_region="ru-central1",
        s3_access_key_id="key",
        s3_secret_access_key="secret",
        s3_prefix="shadowgen-v2-test",
    )
    worker_runtime = build_runtime_adapters(
        state_backend="s3",
        queue_backend="memory",
        state_dir=".shadowgen-ignored",
        s3_endpoint_url="https://storage.example.test",
        s3_bucket="shadowgen-bucket",
        s3_region="ru-central1",
        s3_access_key_id="key",
        s3_secret_access_key="secret",
        s3_prefix="shadowgen-v2-test",
    )

    asset_ref = api_runtime.asset_store.put_bytes(b"source-image", AssetKind.SOURCE, "image/png")
    assert worker_runtime.asset_store.get_bytes(asset_ref.asset_id) == b"source-image"
    source_hash = worker_runtime.asset_store.get_source_hash(asset_ref.asset_id)
    assert isinstance(source_hash, str)
    assert len(source_hash) == 64
    metadata_key = f"shadowgen-v2-test/assets/meta/{asset_ref.asset_id}.json"
    assert fake_client.get_calls_by_key[metadata_key] == 1

    job = JobRecord(
        job_id="job-1",
        status=JobStatus.QUEUED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
        request_cache_key=render_request_key(source_hash, RenderRequest(source_asset_id=asset_ref.asset_id)),
    )
    api_runtime.job_repository.create(job)
    assert worker_runtime.job_repository.get("job-1") is not None
    assert worker_runtime.job_repository.find_by_request_cache_key(job.request_cache_key) is not None
    assert worker_runtime.job_repository.find_by_request_cache_key("missing-cache-key") is None
    assert fake_client.list_calls == 0

    api_runtime.runtime_config_store.update(LocalRuntimeConfig(legacy_ml_base_url="http://ml:9001"))
    assert worker_runtime.runtime_config_store.get().legacy_ml_base_url == "http://ml:9001"

    worker_runtime.worker_state_store.update(WorkerRuntimeState(status="idle", last_job_id="job-1"))
    assert api_runtime.worker_state_store.get().last_job_id == "job-1"

    command = WorkerActionRecord(
        command_id="cmd-1",
        action="restart_worker_process",
        requested_at=datetime.now(timezone.utc),
        requested_by="test",
    )
    api_runtime.worker_action_store.enqueue(command)
    assert worker_runtime.worker_action_store.list_recent(limit=1)[0].command_id == "cmd-1"


def test_s3_job_repository_can_clear_request_cache(monkeypatch) -> None:
    fake_client = FakeS3Client()

    monkeypatch.setattr(
        "shadowgen_adapters.runtime.factories.build_s3_client",
        lambda endpoint_url, bucket_region, access_key_id, secret_access_key: fake_client,
    )

    runtime = build_runtime_adapters(
        state_backend="s3",
        queue_backend="memory",
        state_dir=".shadowgen-ignored",
        s3_endpoint_url="https://storage.example.test",
        s3_bucket="shadowgen-bucket",
        s3_region="ru-central1",
        s3_access_key_id="key",
        s3_secret_access_key="secret",
        s3_prefix="shadowgen-v2-test",
    )
    asset_ref = runtime.asset_store.put_bytes(b"source-image", AssetKind.SOURCE, "image/png")
    cache_key = render_request_key("source-hash", RenderRequest(source_asset_id=asset_ref.asset_id))
    job = JobRecord(
        job_id="job-cache-clear",
        status=JobStatus.SUCCEEDED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
        request_cache_key=cache_key,
        cache_status="miss",
    )
    runtime.job_repository.create(job)
    assert runtime.job_repository.find_by_request_cache_key(cache_key) is not None

    cleared = runtime.job_repository.clear_request_cache()

    assert cleared == 2
    stored = runtime.job_repository.get("job-cache-clear")
    assert stored is not None
    assert stored.request_cache_key is None
    assert stored.cache_status is None
    assert runtime.job_repository.find_by_request_cache_key(cache_key) is None
    assert not any(key.startswith("shadowgen-v2-test/jobs-cache/") for _, key in fake_client.objects)
