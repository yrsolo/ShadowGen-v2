from __future__ import annotations

import base64

import httpx

from shadowgen_adapters.ml_core import MLCorePipelineAdapter
from shadowgen_contracts import RenderRequest, ShadowSettings
from shadowgen_pipeline import PipelineContext


PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="


def build_response(method: str, url: str, payload: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=httpx.Request(method, url))


def test_ml_core_probe_prefers_async_capabilities(monkeypatch) -> None:
    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/health"):
            return build_response("GET", url, {"status": "ok", "async_enabled": True})
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "triton",
                    "async_enabled": True,
                    "components": [
                        {
                            "name": "shadow_generator",
                            "available": True,
                            "backend_kind": "triton",
                            "supports_batching": True,
                            "supports_async": True,
                        }
                    ],
                },
            )
        raise AssertionError(url)

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    adapter = MLCorePipelineAdapter(base_url="http://ml-core:9001")

    summary = adapter.probe(force_refresh=True)

    assert summary.mode == "async"
    assert summary.async_enabled is True
    assert summary.execution_default_backend == "triton"
    assert summary.components[0]["supports_batching"] is True


def test_ml_core_submit_maps_preprocess_and_async_poll(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/health"):
            return build_response("GET", url, {"status": "ok", "async_enabled": True})
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "triton",
                    "async_enabled": True,
                    "components": [],
                },
            )
        if "/v1/render/jobs/" in url:
            return build_response(
                "GET",
                url,
                {
                    "job_id": "ml-job-1",
                    "request_id": "asset-1",
                    "status": "succeeded",
                    "result": {
                        "request_id": "asset-1",
                        "artifacts": [
                            {
                                "name": "final",
                                "kind": "final",
                                "mime_type": "image/png",
                                "image_base64": PNG_BASE64,
                            }
                        ],
                        "metrics": {"total_ms": 321},
                        "warnings": [],
                    },
                },
            )
        raise AssertionError(url)

    def fake_post(url: str, *args, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return build_response(
            "POST",
            url,
            {
                "job_id": "ml-job-1",
                "request_id": "asset-1",
                "status": "queued",
            },
        )

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.post", fake_post)
    adapter = MLCorePipelineAdapter(base_url="http://ml-core:9001")
    context = PipelineContext(
        request=RenderRequest(
            source_asset_id="asset-1",
            preprocess={"padding_px": 144},
            shadow=ShadowSettings(model="v2-diff", angle_deg=35),
        ),
        source_image=base64.b64decode(PNG_BASE64),
        source_mime_type="image/png",
    )

    submission = adapter.submit(context)
    polled = adapter.poll(submission)

    assert submission.mode == "async"
    assert submission.core_job_id == "ml-job-1"
    assert captured["url"] == "http://ml-core:9001/v1/render/jobs"
    assert captured["json"]["preprocess"]["padding_px"] == 144
    assert captured["json"]["source"]["mime_type"] == "image/png"
    assert captured["json"]["source"]["image_base64"] == PNG_BASE64
    assert "data_base64" not in captured["json"]["source"]
    assert captured["json"]["shadow"]["model"] == "v2-diff"
    assert polled.status == "succeeded"
    assert polled.result is not None
    assert polled.result.metrics.total_ms == 321
    assert len(polled.result.artifacts) == 1


def test_ml_core_probe_falls_back_to_legacy_sync(monkeypatch) -> None:
    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/test"):
            return build_response("GET", url, {"ok": True})
        raise httpx.ConnectError("no route", request=httpx.Request("GET", url))

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    adapter = MLCorePipelineAdapter(base_url="http://legacy-shadowgen:9001")

    summary = adapter.probe(force_refresh=True)

    assert summary.mode == "legacy-sync"
    assert summary.async_enabled is False
    assert summary.degraded is True
