import threading

import uvicorn

from shadowgen_adapters.ml_core import MLCorePipelineAdapter
from shadowgen_adapters.runtime import build_runtime_adapters
from shadowgen_application.use_cases.process_job import ProcessJobUseCase

from shadowgen_worker.config import WorkerConfig
from shadowgen_worker.control_actions import WorkerActionExecutor
from shadowgen_worker.control_app import create_worker_control_app
from shadowgen_worker.control_loop import WorkerControlLoop
from shadowgen_worker.executor import JobExecutor
from shadowgen_worker.loop import WorkerLoop
from shadowgen_worker.metadata import collect_worker_version_info
from shadowgen_worker.state import WorkerStateService


def resolve_legacy_base_url(config: WorkerConfig, runtime) -> str | None:
    runtime_config = runtime.runtime_config_store.get()
    return runtime_config.legacy_ml_base_url or config.legacy_ml_base_url


def build_worker_runtime(config: WorkerConfig):
    runtime = build_runtime_adapters(
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
    version_info = collect_worker_version_info(
        repo_path=config.worker_workspace_mount_dest,
        image_tag=config.worker_image_tag,
        container_name=config.worker_container_name,
    )
    state_service = WorkerStateService(
        worker_state_store=runtime.worker_state_store,
        runtime_config_store=runtime.runtime_config_store,
        config_legacy_base_url=config.legacy_ml_base_url,
        version_info=version_info,
        idle_heartbeat_interval_sec=config.worker_state_heartbeat_interval_sec,
    )

    def use_case_factory() -> ProcessJobUseCase:
        pipeline = MLCorePipelineAdapter(
            base_url=resolve_legacy_base_url(config, runtime),
            timeout_sec=config.legacy_ml_timeout_sec,
            capabilities_refresh_interval_sec=config.capabilities_refresh_interval_sec,
        )
        return ProcessJobUseCase(
            job_repository=runtime.job_repository,
            asset_store=runtime.asset_store,
            pipeline=pipeline,
            observer=state_service,
            poll_interval_ms=config.poll_interval_ms,
            job_ttl_ms=config.job_ttl_ms,
            max_retries=config.max_retries,
        )

    executor = JobExecutor(use_case_factory)
    worker_loop = WorkerLoop(
        queue=runtime.job_queue,
        executor=executor,
        state_service=state_service,
        poll_interval_sec=config.poll_interval_sec,
        max_in_flight_jobs=config.max_in_flight_jobs,
    )
    action_executor = WorkerActionExecutor(
        config=config,
        runtime_config_store=runtime.runtime_config_store,
        worker_action_store=runtime.worker_action_store,
        state_service=state_service,
    )
    control_loop = WorkerControlLoop(
        action_store=runtime.worker_action_store,
        executor=action_executor,
        poll_interval_sec=config.control_poll_interval_sec,
    )
    control_app = create_worker_control_app(
        config=config,
        runtime=runtime,
        state_service=state_service,
        version_info=version_info,
    )
    return runtime, state_service, worker_loop, control_loop, control_app


def main():
    config = WorkerConfig()
    print(
        "[ShadowGen Worker] "
        f"state_backend={config.state_backend} "
        f"queue_backend={config.queue_backend} "
        f"s3_bucket={config.s3_bucket} "
        f"legacy_ml_base_url={config.legacy_ml_base_url or 'stub'} "
        f"max_in_flight_jobs={config.max_in_flight_jobs} "
        f"control_port={config.worker_control_port}",
        flush=True,
    )
    _, state_service, worker_loop, control_loop, control_app = build_worker_runtime(config)
    state_service.boot()
    threading.Thread(target=worker_loop.run_forever, daemon=True).start()
    threading.Thread(target=control_loop.run_forever, daemon=True).start()
    uvicorn.run(control_app, host=config.worker_control_host, port=config.worker_control_port)


if __name__ == "__main__":
    main()
