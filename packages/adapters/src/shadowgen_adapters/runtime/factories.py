from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shadowgen_adapters.jobs.s3_job_repository import S3JobRepository
from shadowgen_adapters.object_storage import build_s3_client, normalize_storage_prefix
from shadowgen_adapters.jobs.file_job_repository import FileJobRepository
from shadowgen_adapters.jobs.memory_job_repository import InMemoryJobRepository
from shadowgen_adapters.queue.file_job_queue import FileJobQueue
from shadowgen_adapters.queue.memory_job_queue import InMemoryJobQueue
from shadowgen_adapters.queue.ymq_job_queue import YMQJobQueue
from shadowgen_adapters.runtime.file_runtime_config_store import FileRuntimeConfigStore
from shadowgen_adapters.runtime.file_worker_action_store import FileWorkerActionStore
from shadowgen_adapters.runtime.file_worker_state_store import FileWorkerStateStore
from shadowgen_adapters.runtime.memory_runtime_config_store import MemoryRuntimeConfigStore
from shadowgen_adapters.runtime.memory_worker_action_store import MemoryWorkerActionStore
from shadowgen_adapters.runtime.memory_worker_state_store import MemoryWorkerStateStore
from shadowgen_adapters.runtime.s3_runtime_config_store import S3RuntimeConfigStore
from shadowgen_adapters.runtime.s3_worker_action_store import S3WorkerActionStore
from shadowgen_adapters.runtime.s3_worker_state_store import S3WorkerStateStore
from shadowgen_adapters.storage.file_asset_store import FileAssetStore
from shadowgen_adapters.storage.memory_asset_store import InMemoryAssetStore
from shadowgen_adapters.storage.s3_asset_store import S3AssetStore


@dataclass(slots=True)
class RuntimeAdapters:
    asset_store: object
    job_repository: object
    job_queue: object
    runtime_config_store: object
    worker_state_store: object
    worker_action_store: object


def build_runtime_adapters(
    state_backend: str,
    queue_backend: str,
    state_dir: str,
    s3_endpoint_url: str | None = None,
    s3_bucket: str | None = None,
    s3_region: str = "ru-central1",
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
    s3_prefix: str = "shadowgen-v2",
    ymq_endpoint: str | None = None,
    ymq_queue_url: str | None = None,
    ymq_region: str = "ru-central1",
    ymq_access_key_id: str | None = None,
    ymq_secret_access_key: str | None = None,
    queue_poll_wait_sec: int = 2,
) -> RuntimeAdapters:
    if state_backend == "memory":
        asset_store = InMemoryAssetStore()
        job_repository = InMemoryJobRepository()
        runtime_config_store = MemoryRuntimeConfigStore()
        worker_state_store = MemoryWorkerStateStore()
        worker_action_store = MemoryWorkerActionStore()
    elif state_backend == "s3":
        if not all([s3_endpoint_url, s3_bucket, s3_access_key_id, s3_secret_access_key]):
            raise ValueError("S3 backend requires endpoint, bucket, and credentials.")
        client = build_s3_client(
            endpoint_url=s3_endpoint_url,
            bucket_region=s3_region,
            access_key_id=s3_access_key_id,
            secret_access_key=s3_secret_access_key,
        )
        prefix = normalize_storage_prefix(s3_prefix)
        asset_store = S3AssetStore(client=client, bucket=s3_bucket, prefix=prefix)
        job_repository = S3JobRepository(client=client, bucket=s3_bucket, prefix=prefix)
        runtime_config_store = S3RuntimeConfigStore(client=client, bucket=s3_bucket, prefix=prefix)
        worker_state_store = S3WorkerStateStore(client=client, bucket=s3_bucket, prefix=prefix)
        worker_action_store = S3WorkerActionStore(client=client, bucket=s3_bucket, prefix=prefix)
    else:
        root = Path(state_dir)
        asset_store = FileAssetStore(root / "assets")
        job_repository = FileJobRepository(root / "jobs")
        runtime_config_store = FileRuntimeConfigStore(root)
        worker_state_store = FileWorkerStateStore(root)
        worker_action_store = FileWorkerActionStore(root)

    if queue_backend == "memory":
        job_queue = InMemoryJobQueue()
    elif queue_backend == "ymq":
        if not all([ymq_endpoint, ymq_queue_url, ymq_access_key_id, ymq_secret_access_key]):
            raise ValueError("YMQ backend requires endpoint, queue URL, and credentials.")
        job_queue = YMQJobQueue(
            queue_url=ymq_queue_url,
            endpoint_url=ymq_endpoint,
            region_name=ymq_region,
            access_key_id=ymq_access_key_id,
            secret_access_key=ymq_secret_access_key,
            wait_time_sec=queue_poll_wait_sec,
        )
    else:
        job_queue = FileJobQueue(Path(state_dir) / "queue")

    return RuntimeAdapters(
        asset_store=asset_store,
        job_repository=job_repository,
        job_queue=job_queue,
        runtime_config_store=runtime_config_store,
        worker_state_store=worker_state_store,
        worker_action_store=worker_action_store,
    )
