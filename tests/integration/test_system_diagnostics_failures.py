from datetime import datetime, timezone

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
