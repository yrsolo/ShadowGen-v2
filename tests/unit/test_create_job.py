from shadowgen_adapters.runtime.local_state import asset_store, job_queue, job_repository, reset_local_state
from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_contracts import AssetKind, BackgroundSpec, OutputSpec, RenderRequest, ShadowSettings


def test_create_job_stores_record_and_publishes_queue_item() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    use_case = CreateJobUseCase(job_repository=job_repository, job_queue=job_queue)

    job = use_case.execute(
        CreateJobCommand(
            request=RenderRequest(
                source_asset_id=asset_ref.asset_id,
                shadow=ShadowSettings(),
                background=BackgroundSpec(),
                output=OutputSpec(),
            )
        )
    )

    assert job_repository.get(job.job_id) is not None
    assert job_queue.consume().job_id == job.job_id
