from functools import lru_cache
from hmac import compare_digest

from fastapi import Header, HTTPException

from shadowgen_adapters.runtime import build_runtime_adapters
from shadowgen_adapters.realtime import HttpRealtimeAccelerator, NullRealtimeAccelerator
from shadowgen_application.use_cases import (
    GetJobResultUseCase,
    GetRuntimeConfigUseCase,
    GetSystemDiagnosticsUseCase,
    StorageRuntimeInfo,
    UploadAssetUseCase,
    UpdateRuntimeConfigUseCase,
    WorkerRuntimeInfo,
    CreateWorkerActionUseCase,
    ManageJobUseCase,
)
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase
from shadowgen_api.config import ApiConfig


@lru_cache(maxsize=1)
def get_config() -> ApiConfig:
    return ApiConfig()


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    expected = get_config().admin_api_token
    if not expected or not x_admin_token or not compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token.")


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
    return CreateJobUseCase(
        job_repository=runtime.job_repository,
        job_queue=runtime.job_queue,
        asset_store=runtime.asset_store,
    )


@lru_cache(maxsize=1)
def get_realtime_accelerator():
    config = get_config()
    if (
        not config.vps_accelerator_enabled
        or not config.vps_accelerator_url
        or not config.vps_internal_token
        or not config.vps_realtime_signing_secret
    ):
        return NullRealtimeAccelerator()
    return HttpRealtimeAccelerator(
        base_url=config.vps_accelerator_url,
        internal_token=config.vps_internal_token,
        signing_secret=config.vps_realtime_signing_secret,
        timeout_ms=config.vps_notify_timeout_ms,
        token_ttl_sec=config.vps_realtime_token_ttl_sec,
        fallback_poll_ms=config.vps_realtime_fallback_poll_ms,
    )


def get_get_job_use_case() -> GetJobUseCase:
    runtime = get_runtime()
    return GetJobUseCase(job_repository=runtime.job_repository)


def get_get_job_result_use_case() -> GetJobResultUseCase:
    runtime = get_runtime()
    return GetJobResultUseCase(job_repository=runtime.job_repository)


def get_manage_job_use_case() -> ManageJobUseCase:
    runtime = get_runtime()
    return ManageJobUseCase(job_repository=runtime.job_repository)


def get_upload_asset_use_case() -> UploadAssetUseCase:
    runtime = get_runtime()
    return UploadAssetUseCase(asset_store=runtime.asset_store)


def get_system_diagnostics_use_case() -> GetSystemDiagnosticsUseCase:
    config = get_config()
    runtime = get_runtime()
    runtime_state = runtime.worker_state_store.get()
    runtime_config = runtime.runtime_config_store.get()
    worker_render_backend = "unknown"
    if runtime_state.capabilities and runtime_state.capabilities.execution_default_backend:
        worker_render_backend = runtime_state.capabilities.execution_default_backend
    elif runtime_state.ml_core_mode:
        worker_render_backend = runtime_state.ml_core_mode
    return GetSystemDiagnosticsUseCase(
        app_env=config.app_env,
        job_repository=runtime.job_repository,
        queue_inspector=runtime.job_queue,
        runtime_config_store=runtime.runtime_config_store,
        worker_state_store=runtime.worker_state_store,
        worker_action_store=runtime.worker_action_store,
        worker_runtime=WorkerRuntimeInfo(
            render_backend=worker_render_backend,
            legacy_base_url=runtime_state.effective_legacy_base_url or runtime_config.legacy_ml_base_url or config.legacy_ml_base_url,
            live_legacy_available=None,
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
