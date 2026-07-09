import os
import sys
import threading
import time
from threading import Event
from threading import Lock

import uvicorn

from shadowgen_adapters.ml_core import MLCorePipelineAdapter
from shadowgen_adapters.realtime import HttpRealtimeAccelerator, NullRealtimeAccelerator
from shadowgen_adapters.runtime import build_runtime_adapters
from shadowgen_application.use_cases.process_job import ProcessJobUseCase

from shadowgen_worker.config import WorkerConfig
from shadowgen_worker.control_actions import WorkerActionExecutor
from shadowgen_worker.control_app import create_worker_control_app
from shadowgen_worker.control_loop import WorkerControlLoop
from shadowgen_worker.executor import JobExecutor
from shadowgen_worker.loop import WorkerLoop
from shadowgen_worker.metadata import collect_worker_version_info
from shadowgen_worker.realtime_observer import RealtimePublishingObserver
from shadowgen_worker.realtime_wake import RealtimeWakeListener
from shadowgen_worker.state import WorkerStateService


def _loop_health(loop: object) -> dict:
    last_tick_at = getattr(loop, "last_tick_at_monotonic", None)
    last_tick_age_sec = None
    if last_tick_at is not None:
        last_tick_age_sec = round(time.monotonic() - last_tick_at, 3)
    return {
        "last_tick_age_sec": last_tick_age_sec,
        "last_error": getattr(loop, "last_error", None),
    }


def _background_health(threads: dict[str, threading.Thread], loops: dict[str, object]) -> dict:
    details = {
        name: {
            "alive": thread.is_alive(),
            **_loop_health(loops[name]),
        }
        for name, thread in threads.items()
        if name in loops
    }
    critical_names = ("worker_loop", "control_loop")
    ok = all(details.get(name, {}).get("alive") is True for name in critical_names)
    return {
        "ok": ok,
        "threads": details,
    }


def _restart_if_critical_thread_stops(threads: dict[str, threading.Thread]) -> None:
    while True:
        time.sleep(5.0)
        for name in ("worker_loop", "control_loop"):
            thread = threads.get(name)
            if thread is None or thread.is_alive():
                continue
            print(f"[ShadowGen Worker] critical thread stopped: {name}; restarting process", flush=True)
            os.execv(sys.executable, [sys.executable, "-m", "shadowgen_worker.main"])


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

    pipeline_cache: dict[str | None, MLCorePipelineAdapter] = {}
    pipeline_cache_lock = Lock()
    realtime_accelerator = (
        HttpRealtimeAccelerator(
            base_url=config.vps_accelerator_url,
            internal_token=config.worker_vps_token,
            signing_secret=config.vps_realtime_signing_secret or "worker-no-browser-token-signing",
            timeout_ms=config.vps_event_timeout_ms,
        )
        if config.vps_accelerator_enabled and config.vps_accelerator_url and config.worker_vps_token
        else NullRealtimeAccelerator()
    )
    observer = (
        RealtimePublishingObserver(state_service, realtime_accelerator, worker_id=config.worker_id)
        if config.vps_accelerator_enabled and config.vps_accelerator_url and config.worker_vps_token
        else state_service
    )
    wake_event = Event() if config.vps_accelerator_enabled and config.vps_wake_enabled and config.vps_accelerator_url and config.worker_vps_token else None

    def get_pipeline_adapter() -> MLCorePipelineAdapter:
        base_url = resolve_legacy_base_url(config, runtime)
        with pipeline_cache_lock:
            pipeline = pipeline_cache.get(base_url)
            if pipeline is None:
                pipeline_cache.clear()
                pipeline = MLCorePipelineAdapter(
                    base_url=base_url,
                    timeout_sec=config.legacy_ml_timeout_sec,
                    capabilities_refresh_interval_sec=config.capabilities_refresh_interval_sec,
                )
                pipeline_cache[base_url] = pipeline
            return pipeline

    def use_case_factory() -> ProcessJobUseCase:
        return ProcessJobUseCase(
            job_repository=runtime.job_repository,
            asset_store=runtime.asset_store,
            pipeline=get_pipeline_adapter(),
            observer=observer,
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
        queue_visibility_timeout_sec=config.queue_visibility_timeout_sec,
        queue_visibility_extend_interval_sec=config.queue_visibility_extend_interval_sec,
        wake_event=wake_event,
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
    background_threads: dict[str, threading.Thread] = {}
    background_loops: dict[str, object] = {
        "worker_loop": worker_loop,
        "control_loop": control_loop,
    }
    control_app = create_worker_control_app(
        config=config,
        runtime=runtime,
        state_service=state_service,
        version_info=version_info,
        direct_action_executor=action_executor,
        background_health=lambda: _background_health(background_threads, background_loops),
    )
    wake_listener = (
        RealtimeWakeListener(
            base_url=config.vps_accelerator_url,
            worker_id=config.worker_id,
            worker_token=config.worker_vps_token,
            wake_event=wake_event,
            reconnect_min_sec=config.vps_wake_reconnect_min_sec,
            reconnect_max_sec=config.vps_wake_reconnect_max_sec,
        )
        if wake_event is not None and config.vps_accelerator_url and config.worker_vps_token
        else None
    )
    if wake_listener is not None:
        background_loops["wake_listener"] = wake_listener
    return runtime, state_service, worker_loop, control_loop, control_app, wake_listener, background_threads, background_loops


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
    _, state_service, worker_loop, control_loop, control_app, wake_listener, background_threads, _background_loops = build_worker_runtime(config)
    state_service.boot()
    background_threads["worker_loop"] = threading.Thread(target=worker_loop.run_forever, name="shadowgen-worker-loop", daemon=True)
    background_threads["control_loop"] = threading.Thread(target=control_loop.run_forever, name="shadowgen-control-loop", daemon=True)
    background_threads["worker_loop"].start()
    background_threads["control_loop"].start()
    if wake_listener is not None:
        background_threads["wake_listener"] = threading.Thread(target=wake_listener.run_forever, name="shadowgen-wake-listener", daemon=True)
        background_threads["wake_listener"].start()
    threading.Thread(
        target=_restart_if_critical_thread_stops,
        args=(background_threads,),
        name="shadowgen-loop-supervisor",
        daemon=True,
    ).start()
    uvicorn.run(control_app, host=config.worker_control_host, port=config.worker_control_port)


if __name__ == "__main__":
    main()
