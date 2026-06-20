import pytest

from shadowgen_adapters.runtime.local_state import asset_store, job_repository, reset_local_state
from shadowgen_application.use_cases.process_job import ProcessJobUseCase
from shadowgen_contracts import AssetKind, ErrorInfo, JobRecord, JobStatus, RenderRequest


from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelinePollResult, PipelineSubmission


class ExplodingPipeline:
    def probe(self, force_refresh: bool = False):
        _ = force_refresh
        return PipelineCapabilitiesSummary(mode="sync", async_enabled=False)

    def submit(self, context):
        raise RuntimeError("boom")

    def poll(self, submission):
        raise AssertionError("poll should not be called")

    def cancel(self, submission):
        _ = submission


class FailedPollPipeline:
    def probe(self, force_refresh: bool = False):
        _ = force_refresh
        return PipelineCapabilitiesSummary(mode="async", async_enabled=True)

    def submit(self, context):
        _ = context
        return PipelineSubmission(
            mode="async",
            status="pending",
            core_job_id="ml-job-1",
            request_id="business-job-1",
        )

    def poll(self, submission):
        _ = submission
        return PipelinePollResult(
            status="failed",
            error=ErrorInfo(
                code="validation_error",
                message="pipeline_version must be ml-shadowgen-v1",
                details={"request_id": "business-job-1"},
            ),
            retryable=False,
        )

    def cancel(self, submission):
        _ = submission


class CapturingObserver:
    def __init__(self) -> None:
        self.failed: tuple[str, str, str | None] | None = None

    def capabilities_refreshed(self, snapshot) -> None:
        _ = snapshot

    def job_submitted(self, state) -> None:
        _ = state

    def job_polled(self, state) -> None:
        _ = state

    def job_finished(self, job) -> None:
        _ = job

    def job_failed(self, job_id: str, error_text: str, failure_stage: str | None = None) -> None:
        self.failed = (job_id, error_text, failure_stage)


def test_process_job_marks_failure_on_pipeline_error() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    job = JobRecord(
        job_id="job-failure",
        status=JobStatus.QUEUED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    job_repository.create(job)
    use_case = ProcessJobUseCase(
        job_repository=job_repository,
        asset_store=asset_store,
        pipeline=ExplodingPipeline(),
    )

    with pytest.raises(RuntimeError):
        use_case.execute(job.job_id)

    stored = job_repository.get(job.job_id)
    assert stored is not None
    assert stored.status == JobStatus.FAILED
    assert stored.error is not None
    assert any(stage.name == "ml_submit" and stage.status == "failed" for stage in stored.trace)
    assert stored.trace[-1].name == "failed"


def test_process_job_marks_poll_failure_with_actionable_context() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    job = JobRecord(
        job_id="job-poll-failure",
        status=JobStatus.QUEUED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    job_repository.create(job)
    observer = CapturingObserver()
    use_case = ProcessJobUseCase(
        job_repository=job_repository,
        asset_store=asset_store,
        pipeline=FailedPollPipeline(),
        observer=observer,
        poll_interval_ms=1,
    )

    with pytest.raises(RuntimeError, match="ML poll returned status 'failed'"):
        use_case.execute(job.job_id)

    stored = job_repository.get(job.job_id)
    assert stored is not None
    assert stored.status == JobStatus.FAILED
    assert observer.failed is not None
    assert observer.failed[2] == "ml_poll"
    assert "ml_job_id=ml-job-1" in observer.failed[1]
    assert "validation_error: pipeline_version must be ml-shadowgen-v1" in observer.failed[1]
    assert any(
        stage.name == "ml_submit"
        and stage.status == "succeeded"
        and "ml_job_id=ml-job-1" in (stage.message or "")
        for stage in stored.trace
    )
    assert any(
        stage.name == "ml_poll"
        and stage.status == "failed"
        and "request_id=business-job-1" in (stage.error or "")
        for stage in stored.trace
    )


def test_process_job_redelivery_of_terminal_job_is_noop() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    job = JobRecord(
        job_id="job-terminal",
        status=JobStatus.SUCCEEDED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    job_repository.create(job)
    use_case = ProcessJobUseCase(
        job_repository=job_repository,
        asset_store=asset_store,
        pipeline=ExplodingPipeline(),
    )

    processed = use_case.execute(job.job_id)

    assert processed.status == JobStatus.SUCCEEDED
    assert processed.trace[-1].name == "terminal_noop"
    assert processed.trace[-1].status == "skipped"
