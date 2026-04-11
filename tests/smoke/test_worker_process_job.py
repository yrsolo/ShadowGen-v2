from shadowgen_adapters.legacy_pipeline.adapter import LegacyPipelineAdapter
from shadowgen_adapters.runtime.local_state import asset_store, job_repository, reset_local_state
from shadowgen_application.use_cases.process_job import ProcessJobUseCase
from shadowgen_contracts import AssetKind, JobRecord, JobStatus, RenderRequest


def test_process_job_with_stub_adapter_succeeds() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    job = JobRecord(
        job_id="job-1",
        status=JobStatus.QUEUED,
        request=RenderRequest(source_asset_id=asset_ref.asset_id),
    )
    job_repository.create(job)

    use_case = ProcessJobUseCase(
        job_repository=job_repository,
        asset_store=asset_store,
        pipeline=LegacyPipelineAdapter(base_url=None),
    )

    processed = use_case.execute("job-1")

    assert processed.status == JobStatus.SUCCEEDED
    assert processed.result is not None
    assert len(processed.result.images) == 1
