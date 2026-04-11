from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.local_state import reset_local_state
from shadowgen_api.deps import get_config, get_runtime
from shadowgen_api.main import app


client = TestClient(app)


def test_healthcheck_returns_ok() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_job() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    upload_response = client.post(
        "/v1/assets",
        files={"file": ("source.png", b"image-bytes", "image/png")},
    )
    assert upload_response.status_code == 200
    asset_id = upload_response.json()["asset"]["asset_id"]

    content_response = client.get(f"/v1/assets/{asset_id}/content")
    assert content_response.status_code == 200
    assert content_response.content == b"image-bytes"

    create_response = client.post(
        "/v1/jobs",
        json={
            "render": {
                "source_asset_id": asset_id,
                "pipeline_version": "legacy-black-box-v1",
                "shadow": {
                    "angle_deg": 45,
                    "softness": 0.5,
                    "opacity": 0.6,
                    "reflection": 0.0
                },
                "background": {
                    "mode": "solid",
                    "color_hex": "#FFFFFF"
                },
                "output": {
                    "format": "png",
                    "width": None,
                    "height": None,
                    "return_debug": False
                }
            }
        },
    )
    assert create_response.status_code == 200

    job_id = create_response.json()["job_id"]
    get_response = client.get(f"/v1/jobs/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["job"]["job_id"] == job_id
    assert get_response.json()["job"]["status"] == "queued"

    diagnostics_response = client.get("/v1/system/diagnostics")
    assert diagnostics_response.status_code == 200
    assert diagnostics_response.json()["queue"]["backend"] == "memory"
