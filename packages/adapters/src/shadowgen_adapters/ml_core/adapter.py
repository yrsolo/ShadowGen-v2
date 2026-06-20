from __future__ import annotations

import httpx
from datetime import datetime, timedelta, timezone

from shadowgen_adapters.legacy_pipeline.http_adapter import LegacyHttpAdapter
from shadowgen_adapters.ml_core.errors import MLCoreNonRetryableError, MLCoreRetryableError
from shadowgen_adapters.ml_core.mapper import (
    map_business_request_to_ml_core_request,
    map_ml_core_error_payload,
    map_ml_core_response_to_pipeline_output,
)
from shadowgen_adapters.ml_core.stub_adapter import MLCoreStubAdapter
from shadowgen_contracts import (
    ErrorInfo,
    MLCoreAsyncJobResponse,
    MLCoreAsyncSubmitResponse,
    MLCoreCapabilitiesResponse,
    MLCoreHealthResponse,
    MLCoreRenderResponse,
)
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelineContext, PipelinePollResult, PipelineSubmission


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MLCorePipelineAdapter:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_sec: float = 120.0,
        capabilities_refresh_interval_sec: float = 45.0,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout_sec = timeout_sec
        self.capabilities_refresh_interval_sec = capabilities_refresh_interval_sec
        self._stub = MLCoreStubAdapter()
        self._legacy = LegacyHttpAdapter(self.base_url, timeout_sec) if self.base_url else None
        self._capabilities: PipelineCapabilitiesSummary | None = None
        self._capabilities_expire_at: datetime | None = None

    def probe(self, force_refresh: bool = False) -> PipelineCapabilitiesSummary:
        if self.base_url is None:
            self._capabilities = self._stub.probe(force_refresh=force_refresh)
            return self._capabilities

        now = _utc_now()
        if not force_refresh and self._capabilities is not None and self._capabilities_expire_at and now < self._capabilities_expire_at:
            return self._capabilities

        summary = self._probe_remote()
        self._capabilities = summary
        self._capabilities_expire_at = now + timedelta(seconds=self.capabilities_refresh_interval_sec)
        return summary

    def submit(self, context: PipelineContext) -> PipelineSubmission:
        capabilities = self.probe()
        if self.base_url is None:
            return self._stub.submit(context)

        if capabilities.mode == "legacy-sync":
            assert self._legacy is not None
            output = self._legacy.render(context)
            return PipelineSubmission(mode="sync", status="succeeded", result=output)

        payload = map_business_request_to_ml_core_request(
            request=context.request,
            source_bytes=context.source_image,
            source_mime_type=context.source_mime_type,
            request_id=context.request_id or context.request.source_asset_id,
        )

        try:
            if capabilities.async_enabled:
                response = httpx.post(
                    f"{self.base_url}/v1/render/jobs",
                    json=payload.model_dump(mode="json"),
                    timeout=self.timeout_sec,
                )
                if response.status_code >= 400:
                    self._raise_http_error(response)
                submit = MLCoreAsyncSubmitResponse.model_validate(response.json())
                return PipelineSubmission(
                    mode="async",
                    status=submit.status,
                    core_job_id=submit.job_id,
                    request_id=submit.request_id,
                )

            response = httpx.post(
                f"{self.base_url}/v1/render",
                json=payload.model_dump(mode="json"),
                timeout=self.timeout_sec,
            )
            if response.status_code >= 400:
                self._raise_http_error(response)
            result = MLCoreRenderResponse.model_validate(response.json())
            return PipelineSubmission(
                mode="sync",
                status="succeeded",
                request_id=result.request_id,
                result=map_ml_core_response_to_pipeline_output(result),
            )
        except httpx.TimeoutException as exc:
            raise MLCoreRetryableError(f"ML core timeout: {exc}") from exc
        except httpx.TransportError as exc:
            raise MLCoreRetryableError(f"ML core transport failed: {exc}") from exc

    def poll(self, submission: PipelineSubmission) -> PipelinePollResult:
        if submission.mode != "async" or submission.core_job_id is None:
            if submission.result is not None:
                return PipelinePollResult(status="succeeded", result=submission.result)
            return PipelinePollResult(
                status="failed",
                error=ErrorInfo(code="processing_failed", message="Missing sync result."),
                retryable=False,
            )

        assert self.base_url is not None
        try:
            response = httpx.get(
                f"{self.base_url}/v1/render/jobs/{submission.core_job_id}",
                timeout=min(self.timeout_sec, 30.0),
            )
            if response.status_code >= 400:
                self._raise_http_error(response)
            payload = MLCoreAsyncJobResponse.model_validate(response.json())
            if payload.status in {"pending", "queued", "running"}:
                return PipelinePollResult(status="queued" if payload.status == "pending" else payload.status)
            if payload.status in {"succeeded", "completed"} and payload.result is not None:
                return PipelinePollResult(
                    status="succeeded",
                    result=map_ml_core_response_to_pipeline_output(payload.result),
                )
            if payload.status == "failed":
                error = _normalize_async_error(payload.error, "Async ML core job failed.")
                return PipelinePollResult(status="failed", error=error, retryable=False)
            if payload.status in {"cancelled", "canceled"}:
                error = _normalize_async_error(payload.error, "Async ML core job was cancelled.")
                return PipelinePollResult(status="failed", error=error, retryable=False)
            return PipelinePollResult(
                status="failed",
                error=ErrorInfo(code="processing_failed", message=f"Unknown async status: {payload.status}"),
                retryable=False,
            )
        except httpx.TimeoutException as exc:
            return PipelinePollResult(status="running", error=ErrorInfo(code="timeout", message=str(exc)), retryable=True)
        except httpx.TransportError as exc:
            return PipelinePollResult(status="running", error=ErrorInfo(code="transport_error", message=str(exc)), retryable=True)

    def cancel(self, submission: PipelineSubmission) -> None:
        if not self.base_url or submission.mode != "async" or not submission.core_job_id:
            return
        try:
            httpx.delete(
                f"{self.base_url}/v1/render/jobs/{submission.core_job_id}",
                timeout=min(self.timeout_sec, 10.0),
            )
        except Exception:
            return

    def ping(self) -> bool | None:
        if self.base_url is None:
            return None
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=min(self.timeout_sec, 5.0))
            if 200 <= response.status_code < 300:
                return True
        except Exception:
            pass
        if self._legacy is not None:
            return self._legacy.ping()
        return False

    def _probe_remote(self) -> PipelineCapabilitiesSummary:
        assert self.base_url is not None
        try:
            health_response = httpx.get(f"{self.base_url}/health", timeout=min(self.timeout_sec, 5.0))
            health_response.raise_for_status()
            capabilities_response = httpx.get(f"{self.base_url}/v1/capabilities", timeout=min(self.timeout_sec, 10.0))
            capabilities_response.raise_for_status()
        except Exception as exc:
            if self._legacy is not None and self._legacy.ping():
                return PipelineCapabilitiesSummary(
                    mode="legacy-sync",
                    async_enabled=False,
                    execution_default_backend="legacy-http",
                    refreshed_at_iso=_utc_now().isoformat(),
                    degraded=False,
                    notes=[
                        "Legacy sync compatibility path is active. "
                        "The old ML service does not expose ML-core /health or /v1/capabilities."
                    ],
                )
            raise MLCoreRetryableError(f"ML service handshake failed: {exc}") from exc

        try:
            health = MLCoreHealthResponse.model_validate(health_response.json())
            capabilities = MLCoreCapabilitiesResponse.model_validate(capabilities_response.json())
            supported_modes = set(
                capabilities.supported_submit_modes
                or (("sync", "async") if capabilities.async_enabled else ("sync",))
            )
            preferred_mode = (
                capabilities.preferred_submit_mode
                or health.preferred_submit_mode
                or ("async" if capabilities.async_enabled else "sync")
            )
            prefer_async = (
                health.accepting_jobs
                and health.async_enabled
                and capabilities.async_enabled
                and "async" in supported_modes
                and preferred_mode == "async"
            )
            return PipelineCapabilitiesSummary(
                mode="async" if prefer_async else "sync",
                async_enabled=prefer_async,
                execution_default_backend=capabilities.execution_default_backend,
                refreshed_at_iso=_utc_now().isoformat(),
                degraded=capabilities.degraded or health.status != "ok",
                notes=[] if health.accepting_jobs else ["ML service is not currently accepting async jobs."],
                components=[
                    {
                        "name": component.name,
                        "available": component.available,
                        "backend_kind": component.backend_kind,
                        "model_variant": component.model_variant,
                        "supports_batching": component.supports_batching,
                        "supports_async": component.supports_async,
                        "fallback_reason": component.fallback_reason,
                    }
                    for component in capabilities.components
                ],
            )
        except Exception as exc:
            raise MLCoreRetryableError(f"ML service handshake schema is incompatible: {exc}") from exc

    def _raise_http_error(self, response: httpx.Response) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = {"error": {"code": "processing_failed", "message": response.text}}
        error = map_ml_core_error_payload(payload)
        message = _format_http_error(response, error)
        if response.status_code in {400, 404, 415, 422}:
            raise MLCoreNonRetryableError(message)
        raise MLCoreRetryableError(message)


def _normalize_async_error(error, default_message: str) -> ErrorInfo:
    if error is None:
        return ErrorInfo(code="processing_failed", message=default_message)
    if isinstance(error, str):
        return ErrorInfo(code="processing_failed", message=error)
    return ErrorInfo(code=error.code, message=error.message, details=error.details)


def _format_http_error(response: httpx.Response, error: ErrorInfo) -> str:
    request = response.request
    endpoint = f"{request.method} {request.url.path}"
    message = f"ML core {endpoint} returned HTTP {response.status_code} {error.code}: {error.message}"
    if error.details:
        detail_pairs = ", ".join(f"{key}={value}" for key, value in sorted(error.details.items()))
        return f"{message} ({detail_pairs})"
    return message
