from __future__ import annotations

import base64

import httpx
import pytest

from shadowgen_adapters.ml_core import MLCorePipelineAdapter
from shadowgen_adapters.ml_core.errors import MLCoreNonRetryableError, MLCoreRetryableError
from shadowgen_contracts import RenderRequest, ShadowSettings
from shadowgen_pipeline import PipelineContext


PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="


def build_response(method: str, url: str, payload: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=httpx.Request(method, url))


def test_ml_core_probe_prefers_async_capabilities(monkeypatch) -> None:
    called_urls: list[str] = []

    def fake_get(url: str, *args, **kwargs):
        called_urls.append(url)
        if url.endswith("/health"):
            return build_response(
                "GET",
                url,
                {
                    "status": "ok",
                    "service_version": "0.1.0",
                    "active_backend_mode": "local",
                    "async_enabled": True,
                    "accepting_jobs": True,
                    "preferred_submit_mode": "async",
                },
            )
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "triton",
                    "async_enabled": True,
                    "supported_submit_modes": ["sync", "async"],
                    "preferred_submit_mode": "async",
                    "degraded": False,
                    "components": [
                        {
                            "name": "shadow_generator",
                            "available": True,
                            "backend_kind": "triton",
                            "supports_batching": True,
                            "supports_async": True,
                            "backends": [
                                {
                                    "backend_kind": "local",
                                    "model_variant": "v2-diff",
                                    "model_name": "diffusion-shadow",
                                    "model_version": "1",
                                    "available": True,
                                    "supports_batching": False,
                                    "supports_async": True,
                                }
                            ],
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
    assert not any(url.endswith("/test") for url in called_urls)


def test_ml_core_submit_maps_preprocess_and_async_poll(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/health"):
            return build_response(
                "GET",
                url,
                {
                    "status": "ok",
                    "async_enabled": True,
                    "accepting_jobs": True,
                    "preferred_submit_mode": "async",
                },
            )
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "triton",
                    "async_enabled": True,
                    "supported_submit_modes": ["sync", "async"],
                    "preferred_submit_mode": "async",
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
                    "status": "completed",
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
                        "metrics": {"total_ms": 321, "shadow_ms": 210, "cache_ms": 7},
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
                "status": "pending",
                "submit_mode": "async",
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
        request_id="business-job-1",
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
    assert captured["json"]["pipeline_version"] == "ml-shadowgen-v1"
    assert captured["json"]["shadow"]["model"] == "v2-diff"
    assert captured["json"]["request_id"] == "business-job-1"
    assert polled.status == "succeeded"
    assert polled.result is not None
    assert polled.result.metrics.total_ms == 321
    assert polled.result.metrics.shadow_ms == 210
    assert polled.result.metrics.cache_ms == 7
    assert len(polled.result.artifacts) == 1


def test_ml_core_sync_service_uses_v1_render_for_diffusion(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/health"):
            return build_response(
                "GET",
                url,
                {"status": "ok", "async_enabled": False, "accepting_jobs": True, "preferred_submit_mode": "sync"},
            )
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "local",
                    "async_enabled": False,
                    "supported_submit_modes": ["sync"],
                    "preferred_submit_mode": "sync",
                    "components": [],
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
                "request_id": "business-job-sync",
                "artifacts": [
                    {"name": "final", "kind": "final", "mime_type": "image/png", "image_base64": PNG_BASE64}
                ],
                "metrics": {"total_ms": 500, "shadow_ms": 400},
                "warnings": [],
                "model_info": {"service_version": "0.1.0", "model_version": "v2-diff"},
            },
        )

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.post", fake_post)
    adapter = MLCorePipelineAdapter(base_url="http://ml-core:9001")
    submission = adapter.submit(
        PipelineContext(
            request=RenderRequest(source_asset_id="asset-1", shadow=ShadowSettings(model="v2-diff")),
            source_image=base64.b64decode(PNG_BASE64),
            source_mime_type="image/png",
            request_id="business-job-sync",
        )
    )

    assert submission.mode == "sync"
    assert captured["url"] == "http://ml-core:9001/v1/render"
    assert captured["json"]["pipeline_version"] == "ml-shadowgen-v1"
    assert captured["json"]["shadow"]["model"] == "v2-diff"
    assert captured["json"]["request_id"] == "business-job-sync"
    assert submission.result is not None
    assert submission.result.metrics.shadow_ms == 400


def test_ml_core_submit_error_includes_endpoint_status_and_code(monkeypatch) -> None:
    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/health"):
            return build_response(
                "GET",
                url,
                {"status": "ok", "async_enabled": False, "accepting_jobs": True, "preferred_submit_mode": "sync"},
            )
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "execution_default_backend": "local",
                    "async_enabled": False,
                    "supported_submit_modes": ["sync"],
                    "preferred_submit_mode": "sync",
                    "components": [],
                },
            )
        raise AssertionError(url)

    def fake_post(url: str, *args, **kwargs):
        return build_response(
            "POST",
            url,
            {
                "error": {
                    "code": "validation_error",
                    "message": "pipeline_version must be ml-shadowgen-v1",
                    "request_id": "business-job-sync",
                }
            },
            status_code=422,
        )

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.post", fake_post)
    adapter = MLCorePipelineAdapter(base_url="http://ml-core:9001")

    with pytest.raises(
        MLCoreNonRetryableError,
        match=r"ML core POST /v1/render returned HTTP 422 validation_error: pipeline_version must be ml-shadowgen-v1",
    ):
        adapter.submit(
            PipelineContext(
                request=RenderRequest(source_asset_id="asset-1", shadow=ShadowSettings(model="v2-diff")),
                source_image=base64.b64decode(PNG_BASE64),
                source_mime_type="image/png",
                request_id="business-job-sync",
            )
        )


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
    assert summary.degraded is False
    assert summary.notes == [
        "Legacy sync compatibility path is active. The old ML service does not expose ML-core /health or /v1/capabilities."
    ]


def test_ml_core_probe_does_not_treat_test_404_as_legacy(monkeypatch) -> None:
    def fake_get(url: str, *args, **kwargs):
        if url.endswith("/test"):
            return build_response("GET", url, {"detail": "Not Found"}, status_code=404)
        return build_response("GET", url, {"detail": "Not Found"}, status_code=404)

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    adapter = MLCorePipelineAdapter(base_url="http://unknown-service:9001")

    with pytest.raises(MLCoreRetryableError, match="handshake failed"):
        adapter.probe(force_refresh=True)


def test_ml_core_schema_error_does_not_silently_fall_back_to_legacy(monkeypatch) -> None:
    called_urls: list[str] = []

    def fake_get(url: str, *args, **kwargs):
        called_urls.append(url)
        if url.endswith("/health"):
            return build_response("GET", url, {"status": "ok", "async_enabled": True})
        if url.endswith("/v1/capabilities"):
            return build_response(
                "GET",
                url,
                {
                    "async_enabled": True,
                    "supported_submit_modes": ["sync", "async"],
                    "preferred_submit_mode": "async",
                    "components": [{"name": "shadow_generator", "backends": [{}]}],
                },
            )
        if url.endswith("/test"):
            return build_response("GET", url, {"ok": True})
        raise AssertionError(url)

    monkeypatch.setattr("shadowgen_adapters.ml_core.adapter.httpx.get", fake_get)
    adapter = MLCorePipelineAdapter(base_url="http://ml-core:9001")

    with pytest.raises(MLCoreRetryableError, match="schema is incompatible"):
        adapter.probe(force_refresh=True)
    assert not any(url.endswith("/test") for url in called_urls)
