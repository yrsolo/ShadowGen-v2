from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from shadowgen_contracts import (
    ErrorInfo,
    JobStatus,
    JobRecord,
    RenderResult,
    WorkerCapabilityComponent,
    WorkerCapabilitySnapshot,
    WorkerInFlightJob,
)
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelineContext

from shadowgen_application.ports import (
    AssetStorePort,
    JobRepositoryPort,
    ProcessJobObserverPort,
    RenderPipelinePort,
)
from shadowgen_domain import AssetNotFoundError, JobNotFoundError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessJobUseCase:
    def __init__(
        self,
        job_repository: JobRepositoryPort,
        asset_store: AssetStorePort,
        pipeline: RenderPipelinePort,
        observer: ProcessJobObserverPort | None = None,
        poll_interval_ms: int = 1000,
        job_ttl_ms: int = 300_000,
        max_retries: int = 3,
    ) -> None:
        self.job_repository = job_repository
        self.asset_store = asset_store
        self.pipeline = pipeline
        self.observer = observer
        self.poll_interval_ms = poll_interval_ms
        self.job_ttl_ms = job_ttl_ms
        self.max_retries = max_retries

    def execute(self, job_id: str) -> JobRecord:
        job = self.job_repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job '{job_id}' was not found.")

        source_ref = self.asset_store.get_ref(job.request.source_asset_id)
        if source_ref is None:
            raise AssetNotFoundError(f"Asset '{job.request.source_asset_id}' was not found.")

        job.status = JobStatus.RUNNING
        job.started_at = utc_now()
        job.updated_at = utc_now()
        self.job_repository.update(job)

        try:
            capabilities = self.pipeline.probe()
            self._emit_capabilities(capabilities)
            source_bytes = self.asset_store.get_bytes(job.request.source_asset_id)
            context = PipelineContext(
                request=job.request,
                source_image=source_bytes,
                source_mime_type=source_ref.mime_type,
            )
            submission = self.pipeline.submit(context)
            in_flight = WorkerInFlightJob(
                business_job_id=job.job_id,
                mode=submission.mode,
                status=submission.status,
                ml_core_job_id=submission.core_job_id,
                request_id=submission.request_id,
                submit_started_at=utc_now(),
                ttl_deadline_at=utc_now() + timedelta(milliseconds=self.job_ttl_ms),
            )
            self._emit_job_submitted(in_flight)

            if submission.result is not None:
                processed = self._complete_job(job, submission.result)
                self._emit_job_finished(processed)
                return processed

            poll_retries = 0
            while True:
                if in_flight.ttl_deadline_at is not None and utc_now() > in_flight.ttl_deadline_at:
                    self.pipeline.cancel(submission)
                    raise RuntimeError(
                        f"ML core job '{submission.core_job_id or job.job_id}' exceeded TTL of {self.job_ttl_ms} ms."
                    )

                poll_result = self.pipeline.poll(submission)
                in_flight.status = poll_result.status
                in_flight.last_poll_at = utc_now()
                in_flight.retry_count = poll_retries
                in_flight.last_error = poll_result.error.message if poll_result.error else None
                self._emit_job_polled(in_flight)

                if poll_result.result is not None and poll_result.status in {"succeeded", "completed"}:
                    processed = self._complete_job(job, poll_result.result)
                    self._emit_job_finished(processed)
                    return processed

                if poll_result.status in {"queued", "running", "submitted", "processing"}:
                    if poll_result.error is not None:
                        if not poll_result.retryable or poll_retries >= self.max_retries:
                            raise RuntimeError(poll_result.error.message)
                        poll_retries += 1
                    time.sleep(self.poll_interval_ms / 1000.0)
                    continue

                error = poll_result.error or ErrorInfo(
                    code="processing_failed",
                    message=f"ML core job returned terminal status '{poll_result.status}'.",
                )
                raise RuntimeError(error.message)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.finished_at = utc_now()
            job.updated_at = utc_now()
            job.error = ErrorInfo(code="processing_failed", message=str(exc))
            self.job_repository.update(job)
            self._emit_job_failed(job.job_id, str(exc))
            raise

    def _complete_job(self, job: JobRecord, pipeline_output) -> JobRecord:
        images = []
        debug_images = []
        for artifact in pipeline_output.artifacts:
            asset_ref = self.asset_store.put_bytes(
                data=artifact.data,
                kind=artifact.kind,
                mime_type=artifact.mime_type,
            )
            if artifact.kind.value == "debug":
                debug_images.append(asset_ref)
            else:
                images.append(asset_ref)

        job.result = RenderResult(
            images=images,
            debug_images=debug_images,
            metrics=pipeline_output.metrics,
            warnings=pipeline_output.warnings,
        )
        job.status = JobStatus.SUCCEEDED
        job.finished_at = utc_now()
        job.updated_at = utc_now()
        self.job_repository.update(job)
        return job

    def _emit_capabilities(self, capabilities: PipelineCapabilitiesSummary) -> None:
        if self.observer is None:
            return
        self.observer.capabilities_refreshed(
            WorkerCapabilitySnapshot(
                async_enabled=capabilities.async_enabled,
                execution_default_backend=capabilities.execution_default_backend,
                refreshed_at=_parse_optional_datetime(capabilities.refreshed_at_iso),
                degraded=capabilities.degraded,
                notes=list(capabilities.notes),
                components=[
                    WorkerCapabilityComponent(
                        name=str(component.get("name", "unknown")),
                        available=bool(component.get("available", True)),
                        backend_kind=_coerce_optional_str(component.get("backend_kind")),
                        model_variant=_coerce_optional_str(component.get("model_variant")),
                        supports_batching=bool(component.get("supports_batching", False)),
                        supports_async=bool(component.get("supports_async", False)),
                        fallback_reason=_coerce_optional_str(component.get("fallback_reason")),
                    )
                    for component in capabilities.components
                ],
            )
        )

    def _emit_job_submitted(self, state: WorkerInFlightJob) -> None:
        if self.observer is not None:
            self.observer.job_submitted(state.model_copy(deep=True))

    def _emit_job_polled(self, state: WorkerInFlightJob) -> None:
        if self.observer is not None:
            self.observer.job_polled(state.model_copy(deep=True))

    def _emit_job_finished(self, job: JobRecord) -> None:
        if self.observer is not None:
            self.observer.job_finished(job.model_copy(deep=True))

    def _emit_job_failed(self, job_id: str, error_text: str) -> None:
        if self.observer is not None:
            self.observer.job_failed(job_id, error_text)


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
