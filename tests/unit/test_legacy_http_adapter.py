import base64

from shadowgen_adapters.legacy_pipeline.http_adapter import LegacyHttpAdapter
from shadowgen_contracts import RenderRequest
from shadowgen_pipeline import PipelineContext


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_legacy_http_adapter_uses_old_server_contract(monkeypatch) -> None:
    captured = {}

    def fake_post(url, data, files, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["files"] = files
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "images": [
                    {
                        "kind": "final",
                        "mime": "image/png",
                        "b64": base64.b64encode(PNG_BYTES).decode("ascii"),
                    }
                ],
                "meta": {"timings_ms": {"total": 123}},
                "warnings": ["legacy warning"],
            }
        )

    monkeypatch.setattr("shadowgen_adapters.legacy_pipeline.http_adapter.httpx.post", fake_post)

    adapter = LegacyHttpAdapter("http://legacy-server:9001", timeout_sec=7.0)
    output = adapter.render(
        PipelineContext(
            request=RenderRequest(source_asset_id="asset-1"),
            source_image=b"fake-image",
            source_mime_type="image/png",
        )
    )

    assert captured["url"] == "http://legacy-server:9001/v1/process"
    assert "image" in captured["files"]
    assert "file" not in captured["files"]
    assert set(captured["data"].keys()) == {"rot", "return_debug", "max_objects"}
    assert captured["data"]["rot"] == "45"
    assert output.artifacts[0].mime_type == "image/png"
    assert output.artifacts[0].data == PNG_BYTES
    assert output.metrics.total_ms == 123
    assert output.warnings == ["legacy warning"]


def test_legacy_http_adapter_rounds_angle_for_legacy_int_parser(monkeypatch) -> None:
    captured = {}

    def fake_post(url, data, files, timeout):
        captured["data"] = data
        return FakeResponse(
            {
                "images": [
                    {
                        "kind": "final",
                        "mime": "image/png",
                        "b64": base64.b64encode(PNG_BYTES).decode("ascii"),
                    }
                ],
                "meta": {"timings_ms": {"total": 0}},
                "warnings": [],
            }
        )

    monkeypatch.setattr("shadowgen_adapters.legacy_pipeline.http_adapter.httpx.post", fake_post)

    adapter = LegacyHttpAdapter("http://legacy-server:9001", timeout_sec=7.0)
    adapter.render(
        PipelineContext(
            request=RenderRequest.model_validate(
                {
                    "source_asset_id": "asset-1",
                    "shadow": {"angle_deg": 44.6},
                }
            ),
            source_image=b"fake-image",
            source_mime_type="image/png",
        )
    )

    assert captured["data"]["rot"] == "45"


def test_legacy_http_adapter_ping_uses_test_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse({}, status_code=200)

    monkeypatch.setattr("shadowgen_adapters.legacy_pipeline.http_adapter.httpx.get", fake_get)

    adapter = LegacyHttpAdapter("http://legacy-server:9001", timeout_sec=7.0)
    assert adapter.ping() is True
    assert captured["url"] == "http://legacy-server:9001/test"


def test_legacy_http_adapter_ping_rejects_test_404(monkeypatch) -> None:
    monkeypatch.setattr(
        "shadowgen_adapters.legacy_pipeline.http_adapter.httpx.get",
        lambda url, timeout: FakeResponse({"detail": "Not Found"}, status_code=404),
    )

    adapter = LegacyHttpAdapter("http://new-server:9001", timeout_sec=7.0)

    assert adapter.ping() is False
