from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.local_state import reset_local_state
from shadowgen_api.deps import get_config, get_runtime
from shadowgen_api.main import app


client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Token": "change-me-shadowgen-admin"}


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
    assert content_response.headers["cache-control"] == "public, max-age=31536000, immutable"

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


def test_create_job_reuses_cached_job_for_same_image_and_params() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    upload_response = client.post(
        "/v1/assets",
        files={"file": ("source.png", b"same-image", "image/png")},
    )
    assert upload_response.status_code == 200
    asset_id = upload_response.json()["asset"]["asset_id"]

    payload = {
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
    }

    first = client.post("/v1/jobs", json=payload)
    assert first.status_code == 200
    second = client.post("/v1/jobs", json=payload)
    assert second.status_code == 200

    assert second.json()["job_id"] == first.json()["job_id"]


def test_admin_can_mark_job_failed_and_delete_it() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()
    upload_response = client.post(
        "/v1/assets",
        files={"file": ("source.png", b"operator-image", "image/png")},
    )
    asset_id = upload_response.json()["asset"]["asset_id"]
    create_response = client.post(
        "/v1/jobs",
        json={
            "render": {
                "source_asset_id": asset_id,
                "pipeline_version": "legacy-black-box-v1",
                "shadow": {"angle_deg": 45, "softness": 0.5, "opacity": 0.6, "reflection": 0.0},
                "background": {"mode": "solid", "color_hex": "#FFFFFF"},
                "output": {"format": "png", "width": None, "height": None, "return_debug": False},
            }
        },
    )
    job_id = create_response.json()["job_id"]

    denied = client.post(f"/v1/jobs/{job_id}/mark-failed", json={"reason": "lost"})
    assert denied.status_code == 401

    marked = client.post(
        f"/v1/jobs/{job_id}/mark-failed",
        headers=ADMIN_HEADERS,
        json={"reason": "lost in queue"},
    )
    assert marked.status_code == 200
    assert marked.json()["status"] == "failed"
    assert client.get(f"/v1/jobs/{job_id}").json()["job"]["error"]["message"] == "lost in queue"

    deleted = client.delete(f"/v1/jobs/{job_id}", headers=ADMIN_HEADERS)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/v1/jobs/{job_id}").status_code == 404
