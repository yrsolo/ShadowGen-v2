from shadowgen_adapters.runtime.factories import build_runtime_adapters

_runtime = build_runtime_adapters(state_backend="memory", queue_backend="memory", state_dir=".shadowgen-test")
job_repository = _runtime.job_repository
job_queue = _runtime.job_queue
asset_store = _runtime.asset_store
runtime_config_store = _runtime.runtime_config_store
worker_state_store = _runtime.worker_state_store


def reset_local_state() -> None:
    if hasattr(job_repository, "clear"):
        job_repository.clear()
    if hasattr(job_queue, "clear"):
        job_queue.clear()
    if hasattr(asset_store, "clear"):
        asset_store.clear()
    if hasattr(runtime_config_store, "update"):
        runtime_config_store.update(type(runtime_config_store.get())())
    if hasattr(worker_state_store, "update"):
        worker_state_store.update(type(worker_state_store.get())())
