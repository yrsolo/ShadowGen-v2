from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.local_state import reset_local_state
from shadowgen_api.deps import get_config, get_runtime
from shadowgen_api.main import app


client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Token": "change-me-shadowgen-admin"}


def test_runtime_config_can_be_read_and_updated() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()

    initial = client.get("/v1/system/runtime-config")
    assert initial.status_code == 200
    assert initial.json()["legacy_ml_base_url"] is None

    updated = client.put(
        "/v1/system/runtime-config",
        headers=ADMIN_HEADERS,
        json={"legacy_ml_base_url": "http://192.168.1.11:9001"},
    )
    assert updated.status_code == 200
    assert updated.json()["config"]["legacy_ml_base_url"] == "http://192.168.1.11:9001"

    fetched = client.get("/v1/system/runtime-config")
    assert fetched.status_code == 200
    assert fetched.json()["legacy_ml_base_url"] == "http://192.168.1.11:9001"


def test_runtime_config_update_requires_admin_token() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()

    response = client.put(
        "/v1/system/runtime-config",
        json={"legacy_ml_base_url": "http://192.168.1.11:9001"},
    )

    assert response.status_code == 401
