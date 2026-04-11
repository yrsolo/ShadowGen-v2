from __future__ import annotations

import base64

import httpx

from shadowgen_contracts import AssetKind, ProcessingMetrics
from shadowgen_pipeline import PipelineArtifact, PipelineContext, PipelineOutput

from .base import build_stub_output
from .mapper import map_render_request_to_legacy_payload


class LegacyHttpAdapter:
    def __init__(self, base_url: str, timeout_sec: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def render(self, context: PipelineContext) -> PipelineOutput:
        payload = map_render_request_to_legacy_payload(context.request)
        files = {"image": ("source.png", context.source_image, context.source_mime_type)}
        response = httpx.post(
            f"{self.base_url}/v1/process",
            data=payload,
            files=files,
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        data = response.json()

        artifacts = []
        for image_payload in data.get("images", []):
            encoded = image_payload.get("b64")
            if not encoded:
                continue
            image_bytes = base64.b64decode(encoded)
            kind = AssetKind.DEBUG if image_payload.get("kind") == "debug" else AssetKind.FINAL
            artifacts.append(
                PipelineArtifact(
                    kind=kind,
                    mime_type=image_payload.get("mime", "image/png"),
                    data=image_bytes,
                )
            )

        if not artifacts:
            return build_stub_output(["Legacy HTTP adapter returned no image artifacts."])

        metrics = ProcessingMetrics(total_ms=int(data.get("meta", {}).get("timings_ms", {}).get("total", 0)))
        return PipelineOutput(
            artifacts=artifacts,
            metrics=metrics,
            warnings=data.get("warnings", []),
        )

    def ping(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/test", timeout=min(self.timeout_sec, 5.0))
            return response.status_code < 500
        except Exception:
            return False
