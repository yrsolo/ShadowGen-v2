from shadowgen_adapters.jobs.memory_job_repository import InMemoryJobRepository
from shadowgen_adapters.legacy_pipeline.base import build_stub_output
from shadowgen_adapters.storage.memory_asset_store import InMemoryAssetStore
from shadowgen_application.use_cases.process_job import ProcessJobUseCase
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, RenderRequest
from shadowgen_pipeline import PipelineCapabilitiesSummary, PipelinePollResult, PipelineSubmission


class CountingJobRepository(InMemoryJobRepository):
    def __init__(self) -> None:
        super().__init__()
        self.update_count = 0

    def update(self, job: JobRecord) -> None:
        self.update_count += 1
        super().update(job)


class ImmediateAsyncPipeline:
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
        return PipelinePollResult(status="succeeded", result=build_stub_output())

    def cancel(self, submission):
        _ = submission


def test_process_job_buffers_fast_stage_metadata_writes() -> None:
    asset_store = InMemoryAssetStore()
    job_repository = CountingJobRepository()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    job = JobRecord(
        job_id="job-buffered-writes",
        status=JobStatus.QUEUED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    job_repository.create(job)

    processed = ProcessJobUseCase(
        job_repository=job_repository,
        asset_store=asset_store,
        pipeline=ImmediateAsyncPipeline(),
        poll_interval_ms=1,
    ).execute(job.job_id)

    assert processed.status == JobStatus.SUCCEEDED
    assert job_repository.update_count == 4
    assert [stage.name for stage in processed.trace] == [
        "worker_claimed",
        "asset_ref_loaded",
        "ml_probe",
        "asset_bytes_loaded",
        "ml_submit",
        "ml_poll",
        "artifact_store",
        "completed",
    ]
