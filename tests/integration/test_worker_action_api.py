from fastapi.testclient import TestClient

from shadowgen_adapters.runtime.local_state import reset_local_state
from shadowgen_api.deps import get_config, get_runtime
from shadowgen_api.main import app


client = TestClient(app)


def test_worker_action_can_be_enqueued_via_api() -> None:
    reset_local_state()
    get_config.cache_clear()
    get_runtime.cache_clear()

    response = client.post("/v1/system/worker-actions", json={"action": "restart_worker_process"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["command"]["action"] == "restart_worker_process"
    assert payload["command"]["status"] == "queued"

    diagnostics = client.get("/v1/system/diagnostics")
    assert diagnostics.status_code == 200
    assert diagnostics.json()["worker"]["recent_actions"][0]["action"] == "restart_worker_process"
