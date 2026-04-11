from functools import lru_cache

from shadowgen_adapters.legacy_pipeline.adapter import LegacyPipelineAdapter
from shadowgen_adapters.runtime import build_runtime_adapters
from shadowgen_application.use_cases import (
    GetJobResultUseCase,
    GetRuntimeConfigUseCase,
    GetSystemDiagnosticsUseCase,
    StorageRuntimeInfo,
    UploadAssetUseCase,
    UpdateRuntimeConfigUseCase,
    WorkerRuntimeInfo,
    CreateWorkerActionUseCase,
)
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase
from shadowgen_api.config import ApiConfig


@lru_cache(maxsize=1)
def get_config() -> ApiConfig:
    return ApiConfig()


@lru_cache(maxsize=1)
def get_runtime():
    config = get_config()
    return build_runtime_adapters(
        state_backend=config.state_backend,
        queue_backend=config.queue_backend,
        state_dir=config.state_dir,
        s3_endpoint_url=config.s3_endpoint_url,
        s3_bucket=config.s3_bucket,
        s3_region=config.s3_region,
        s3_access_key_id=config.s3_access_key_id,
        s3_secret_access_key=config.s3_secret_access_key,
        s3_prefix=config.s3_prefix,
        ymq_endpoint=config.ymq_endpoint,
        ymq_queue_url=config.ymq_queue_url,
        ymq_region=config.ymq_region,
        ymq_access_key_id=config.ymq_access_key_id,
        ymq_secret_access_key=config.ymq_secret_access_key,
        queue_poll_wait_sec=config.queue_poll_wait_sec,
    )


def get_create_job_use_case() -> CreateJobUseCase:
    runtime = get_runtime()
    return CreateJobUseCase(job_repository=runtime.job_repository, job_queue=runtime.job_queue)


def get_get_job_use_case() -> GetJobUseCase:
    runtime = get_runtime()
    return GetJobUseCase(job_repository=runtime.job_repository)


def get_get_job_result_use_case() -> GetJobResultUseCase:
    runtime = get_runtime()
    return GetJobResultUseCase(job_repository=runtime.job_repository)


def get_upload_asset_use_case() -> UploadAssetUseCase:
    runtime = get_runtime()
    return UploadAssetUseCase(asset_store=runtime.asset_store)


def get_system_diagnostics_use_case() -> GetSystemDiagnosticsUseCase:
    config = get_config()
    runtime = get_runtime()
    pipeline = LegacyPipelineAdapter(
        base_url=config.legacy_ml_base_url,
        timeout_sec=config.legacy_ml_timeout_sec,
    )
    return GetSystemDiagnosticsUseCase(
        app_env=config.app_env,
        job_repository=runtime.job_repository,
        queue_inspector=runtime.job_queue,
        runtime_config_store=runtime.runtime_config_store,
        worker_state_store=runtime.worker_state_store,
        worker_action_store=runtime.worker_action_store,
        worker_runtime=WorkerRuntimeInfo(
            render_backend="legacy-http" if (runtime.runtime_config_store.get().legacy_ml_base_url or config.legacy_ml_base_url) else "legacy-stub",
            legacy_base_url=runtime.runtime_config_store.get().legacy_ml_base_url or config.legacy_ml_base_url,
            live_legacy_available=pipeline.ping(),
        ),
        storage_runtime=StorageRuntimeInfo(
            backend=config.state_backend,
            bucket=config.s3_bucket,
            prefix=config.s3_prefix if config.state_backend == "s3" else None,
            notes=(
                [f"S3 target: {config.s3_endpoint_url} / {config.s3_bucket} / {config.s3_prefix}"]
                if config.state_backend == "s3"
                else ["Local file-backed state is enabled."]
            ),
        ),
    )


def get_runtime_config_use_case() -> GetRuntimeConfigUseCase:
    runtime = get_runtime()
    return GetRuntimeConfigUseCase(runtime_config_store=runtime.runtime_config_store)


def get_update_runtime_config_use_case() -> UpdateRuntimeConfigUseCase:
    runtime = get_runtime()
    return UpdateRuntimeConfigUseCase(runtime_config_store=runtime.runtime_config_store)


def get_create_worker_action_use_case() -> CreateWorkerActionUseCase:
    runtime = get_runtime()
    return CreateWorkerActionUseCase(worker_action_store=runtime.worker_action_store)


def get_asset_store():
    return get_runtime().asset_store
