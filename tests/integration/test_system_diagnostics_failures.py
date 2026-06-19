from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.local_state import reset_local_state
from shadowgen_api.deps import get_config, get_runtime
from shadowgen_api.main import app
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, RenderRequest, WorkerRuntimeState


client = TestClient(app)


def test_diagnostics_include_worker_state_and_failures() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    runtime = get_runtime()

    asset_ref = runtime.asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    failed_job = JobRecord(
        job_id="job-failed",
        status=JobStatus.FAILED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    runtime.job_repository.create(failed_job)
    runtime.worker_state_store.update(
        WorkerRuntimeState(
            status="error",
            last_job_id="job-failed",
            last_error="HTTP 400 from legacy ML",
            updated_at=datetime.now(timezone.utc),
        )
    )

    response = client.get("/v1/system/diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["storage"]["backend"] == "memory"
    assert payload["worker"]["runtime_state"]["status"] == "error"
    assert payload["worker"]["heartbeat_age_sec"] is not None
    assert payload["worker"]["failed_jobs_count"] >= 1
    assert payload["worker"]["recent_failures"][0]["job_id"] == "job-failed"


def test_worker_heartbeat_is_stale_after_five_minutes() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    runtime = get_runtime()

    runtime.worker_state_store.update(
        WorkerRuntimeState(
            status="idle",
            updated_at=datetime.now(timezone.utc) - timedelta(seconds=301),
        )
    )

    response = client.get("/v1/system/diagnostics")
    assert response.status_code == 200
    assert response.json()["worker"]["heartbeat_is_stale"] is True


def test_diagnostics_prioritize_active_jobs_over_recent_completed_jobs() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    runtime = get_runtime()

    active_asset = runtime.asset_store.put_bytes(b"active-image", AssetKind.SOURCE, "image/png")
    runtime.job_repository.create(
        JobRecord(
            job_id="job-active-old",
            status=JobStatus.RUNNING,
            request=RenderRequest(source_asset_id=active_asset.asset_id),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
    )
    for index in range(12):
        asset_ref = runtime.asset_store.put_bytes(f"done-{index}".encode(), AssetKind.SOURCE, "image/png")
        runtime.job_repository.create(
            JobRecord(
                job_id=f"job-done-{index}",
                status=JobStatus.SUCCEEDED,
                request=RenderRequest(source_asset_id=asset_ref.asset_id),
                updated_at=datetime.now(timezone.utc) - timedelta(minutes=index),
            )
        )

    response = client.get("/v1/system/diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["lost_jobs"][0]["job"]["job_id"] == "job-active-old"
    assert "worker runtime state does not list this job" in " ".join(payload["lost_jobs"][0]["evidence"])
