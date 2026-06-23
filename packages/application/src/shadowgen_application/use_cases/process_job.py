from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from shadowgen_contracts import (
    ErrorInfo,
    JobRecord,
    JobStatus,
    JobTraceStage,
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
from shadowgen_domain import AssetNotFoundError, JobEntity, JobNotFoundError, JobStatus as DomainJobStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessJobUseCase:
    def __init__(
        self,
        job_repository: JobRepositoryPort,
        asset_store: AssetStorePort,
        pipeline: RenderPipelinePort,
        observer: ProcessJobObserverPort | None = None,
        poll_interval_ms: int = 200,
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
        if DomainJobStatus(job.status.value).is_terminal:
            self._record_stage(job, "terminal_noop", "skipped", message=f"Job is already {job.status.value}.")
            self.job_repository.update(job)
            return job

        self._start_stage(job, "worker_claimed", "Worker claimed the queued job.")
        self._finish_stage(job, "worker_claimed", "succeeded")
        self.job_repository.update(job)

        self._start_stage(job, "asset_ref_loaded", "Loading source asset reference.")
        source_ref = self.asset_store.get_ref(job.request.source_asset_id)
        if source_ref is None:
            self._finish_stage(job, "asset_ref_loaded", "failed", error=f"Asset '{job.request.source_asset_id}' was not found.")
            self.job_repository.update(job)
            raise AssetNotFoundError(f"Asset '{job.request.source_asset_id}' was not found.")
        self._finish_stage(job, "asset_ref_loaded", "succeeded", message=f"Source MIME type: {source_ref.mime_type}.")

        domain_job = _to_domain_job(job)
        domain_job.start(utc_now())
        _apply_domain_job(job, domain_job)
        self.job_repository.update(job)

        try:
            self._start_stage(job, "ml_probe", "Checking worker-side ML capabilities.")
            self.job_repository.update(job)
            capabilities = self.pipeline.probe()
            self._emit_capabilities(capabilities)
            self._finish_stage(
                job,
                "ml_probe",
                "succeeded",
                message=f"Mode: {'async' if capabilities.async_enabled else 'sync'}; degraded: {capabilities.degraded}.",
            )
            self.job_repository.update(job)

            self._start_stage(job, "asset_bytes_loaded", "Loading source image bytes.")
            self.job_repository.update(job)
            source_bytes = self.asset_store.get_bytes(job.request.source_asset_id)
            self._finish_stage(job, "asset_bytes_loaded", "succeeded", message=f"Loaded {len(source_bytes)} bytes.")
            self.job_repository.update(job)

            context = PipelineContext(
                request=job.request,
                source_image=source_bytes,
                source_mime_type=source_ref.mime_type,
                request_id=job.job_id,
            )
            self._start_stage(job, "ml_submit", "Submitting render request to ML.")
            self.job_repository.update(job)
            submission = self.pipeline.submit(context)
            self._finish_stage(job, "ml_submit", "succeeded", message=_submission_message(submission))
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

            self._start_stage(job, "ml_poll", "Waiting for async ML completion.")
            self.job_repository.update(job)
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
                    self._finish_stage(job, "ml_poll", "succeeded", message=f"Completed after {poll_retries} retries.")
                    processed = self._complete_job(job, poll_result.result)
                    self._emit_job_finished(processed)
                    return processed

                if poll_result.status in {"queued", "running", "submitted", "processing"}:
                    if poll_result.error is not None:
                        if not poll_result.retryable or poll_retries >= self.max_retries:
                            raise RuntimeError(_poll_error_message(submission, poll_result))
                        poll_retries += 1
                    time.sleep(self.poll_interval_ms / 1000.0)
                    continue

                error = poll_result.error or ErrorInfo(
                    code="processing_failed",
                    message=f"ML core job returned terminal status '{poll_result.status}'.",
                )
                raise RuntimeError(_poll_error_message(submission, poll_result, error))
        except Exception as exc:
            self._fail_running_stage(job, str(exc))
            failure_stage = _last_failed_stage_name(job)
            domain_job = _to_domain_job(job)
            if not domain_job.is_terminal:
                domain_job.fail(utc_now())
                _apply_domain_job(job, domain_job)
            job.error = ErrorInfo(code="processing_failed", message=str(exc))
            self._record_stage(job, "failed", "failed", message="Job processing failed.", error=str(exc))
            self.job_repository.update(job)
            self._emit_job_failed(job.job_id, str(exc), failure_stage)
            raise

    def _complete_job(self, job: JobRecord, pipeline_output) -> JobRecord:
        self._start_stage(job, "artifact_store", "Storing generated artifacts.")
        self.job_repository.update(job)
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
        self._finish_stage(job, "artifact_store", "succeeded", message=f"Stored {len(images)} final and {len(debug_images)} debug artifacts.")

        job.result = RenderResult(
            images=images,
            debug_images=debug_images,
            metrics=pipeline_output.metrics,
            warnings=pipeline_output.warnings,
        )
        domain_job = _to_domain_job(job)
        domain_job.complete(utc_now())
        _apply_domain_job(job, domain_job)
        self._record_stage(job, "completed", "succeeded", message="Job completed successfully.")
        self.job_repository.update(job)
        return job

    def _start_stage(self, job: JobRecord, name: str, message: str | None = None) -> None:
        job.trace.append(JobTraceStage(name=name, status="running", message=message))

    def _finish_stage(
        self,
        job: JobRecord,
        name: str,
        status: str,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        now = utc_now()
        for stage in reversed(job.trace):
            if stage.name == name and stage.status == "running" and stage.finished_at is None:
                stage.status = status
                stage.finished_at = now
                stage.duration_ms = int((now - stage.started_at).total_seconds() * 1000)
                if message is not None:
                    stage.message = message
                stage.error = error
                return
        self._record_stage(job, name, status, message=message, error=error)

    def _fail_running_stage(self, job: JobRecord, error: str) -> None:
        now = utc_now()
        for stage in reversed(job.trace):
            if stage.status == "running" and stage.finished_at is None:
                stage.status = "failed"
                stage.finished_at = now
                stage.duration_ms = int((now - stage.started_at).total_seconds() * 1000)
                stage.error = error
                return

    def _record_stage(
        self,
        job: JobRecord,
        name: str,
        status: str,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        stage = JobTraceStage(name=name, status=status, message=message, error=error)
        stage.finished_at = stage.started_at
        stage.duration_ms = 0
        job.trace.append(stage)

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

    def _emit_job_failed(self, job_id: str, error_text: str, failure_stage: str | None) -> None:
        if self.observer is not None:
            self.observer.job_failed(job_id, error_text, failure_stage)


def _parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _last_failed_stage_name(job: JobRecord) -> str | None:
    for stage in reversed(job.trace):
        if stage.status == "failed":
            return stage.name
    return None


def _submission_message(submission) -> str:
    parts = [f"{submission.mode} / {submission.status}"]
    if submission.core_job_id:
        parts.append(f"ml_job_id={submission.core_job_id}")
    if submission.request_id:
        parts.append(f"request_id={submission.request_id}")
    return "; ".join(parts) + "."


def _poll_error_message(submission, poll_result, error: ErrorInfo | None = None) -> str:
    payload_error = error or poll_result.error
    parts = [f"ML poll returned status '{poll_result.status}'"]
    if submission.core_job_id:
        parts.append(f"ml_job_id={submission.core_job_id}")
    if submission.request_id:
        parts.append(f"request_id={submission.request_id}")
    if payload_error is not None:
        parts.append(f"{payload_error.code}: {payload_error.message}")
        if payload_error.details:
            details = ", ".join(f"{key}={value}" for key, value in sorted(payload_error.details.items()))
            parts.append(f"details=({details})")
    return "; ".join(parts)


def _to_domain_job(job: JobRecord) -> JobEntity:
    return JobEntity(
        job_id=job.job_id,
        status=DomainJobStatus(job.status.value),
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _apply_domain_job(job: JobRecord, domain_job: JobEntity) -> None:
    job.status = JobStatus(domain_job.status.value)
    job.created_at = domain_job.created_at
    job.updated_at = domain_job.updated_at
    job.started_at = domain_job.started_at
    job.finished_at = domain_job.finished_at
