from datetime import datetime, timezone

from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.factories import build_runtime_adapters
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, RenderRequest, WorkerVersionInfo
from shadowgen_worker.config import WorkerConfig
from shadowgen_worker.control_app import create_worker_control_app
from shadowgen_worker.state import WorkerStateService


def test_worker_control_app_serves_status_and_accepts_tokenized_action() -> None:
    runtime = build_runtime_adapters(
        state_backend="memory",
        queue_backend="memory",
        state_dir=".shadowgen-test",
    )
    config = WorkerConfig(worker_control_token="secret-token")
    state_service = WorkerStateService(
        worker_state_store=runtime.worker_state_store,
        runtime_config_store=runtime.runtime_config_store,
        config_legacy_base_url="http://ml:9001",
        version_info=WorkerVersionInfo(git_branch="main", git_commit="abc123"),
    )
    state_service.boot()

    asset_ref = runtime.asset_store.put_bytes(b"img", AssetKind.SOURCE, "image/png")
    result_ref = runtime.asset_store.put_bytes(
        b"\x89PNG\r\n\x1a\n",
        AssetKind.FINAL,
        "image/png",
    )
    runtime.job_repository.create(
        JobRecord(
            job_id="job-ok",
            status=JobStatus.SUCCEEDED,
            request=RenderRequest(source_asset_id=asset_ref.asset_id),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            result={
                "images": [result_ref.model_dump(mode="json")],
                "debug_images": [],
                "metrics": {"total_ms": 10},
                "warnings": [],
            },
        )
    )

    app = create_worker_control_app(
        config=config,
        runtime=runtime,
        state_service=state_service,
        version_info=WorkerVersionInfo(git_branch="main", git_commit="abc123"),
    )
    client = TestClient(app)

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["worker"]["status"] == "idle"
    assert status.json()["self_management"]["enabled"] is False
    assert status.json()["self_management"]["mode"] == "self-contained"
    assert len(status.json()["recent_completed_jobs"][0]["finished_at_display"]) >= 19
    assert status.json()["recent_completed_jobs"][0]["preview_url"] == "/api/jobs/job-ok/preview"

    preview = client.get("/api/jobs/job-ok/preview")
    assert preview.status_code == 200
    assert preview.content == b"\x89PNG\r\n\x1a\n"
    assert preview.headers["content-type"] == "image/png"

    denied = client.post("/api/actions/restart", json={"action": "restart_worker_process"})
    assert denied.status_code == 401

    accepted = client.post(
        "/api/actions/restart",
        json={"action": "restart_worker_process"},
        headers={"X-Worker-Token": "secret-token"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["command"]["action"] == "restart_worker_process"
