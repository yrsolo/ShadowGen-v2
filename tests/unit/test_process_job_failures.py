import pytest

from shadowgen_adapters.runtime.local_state import asset_store, job_repository, reset_local_state
from shadowgen_application.use_cases.process_job import ProcessJobUseCase
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, RenderRequest


from shadowgen_pipeline import PipelineCapabilitiesSummary


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
