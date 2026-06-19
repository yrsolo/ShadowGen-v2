from datetime import datetime, timedelta, timezone

from shadowgen_adapters.runtime.local_state import asset_store, job_queue, job_repository, reset_local_state
from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_contracts import AssetKind, BackgroundSpec, JobStatus, OutputSpec, RenderRequest, ShadowSettings


def test_create_job_stores_record_and_publishes_queue_item() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    use_case = CreateJobUseCase(job_repository=job_repository, job_queue=job_queue, asset_store=asset_store)

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
    assert job.cache_status == "miss"
    assert job.reused_existing_job is False
    assert [stage.name for stage in job.trace] == ["created", "cache_lookup", "queued"]


def test_create_job_reuses_cached_succeeded_job_without_queueing_duplicate() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"same-image", AssetKind.SOURCE, "image/png")
    use_case = CreateJobUseCase(job_repository=job_repository, job_queue=job_queue, asset_store=asset_store)

    first = use_case.execute(
        CreateJobCommand(
            request=RenderRequest(
                source_asset_id=asset_ref.asset_id,
                shadow=ShadowSettings(angle_deg=60),
                background=BackgroundSpec(),
                output=OutputSpec(),
            )
        )
    )
    stored = job_repository.get(first.job_id)
    assert stored is not None
    stored.status = JobStatus.SUCCEEDED
    job_repository.update(stored)
    assert job_queue.consume().job_id == first.job_id

    second = use_case.execute(
        CreateJobCommand(
            request=RenderRequest(
                source_asset_id=asset_ref.asset_id,
                shadow=ShadowSettings(angle_deg=60),
                background=BackgroundSpec(),
                output=OutputSpec(),
            )
        )
    )

    assert second.job_id == first.job_id
    assert second.cache_status == "hit-succeeded"
    assert second.reused_existing_job is True
    assert job_queue.consume() is None


def test_create_job_does_not_reuse_stale_live_cache_record() -> None:
    reset_local_state()
    asset_ref = asset_store.put_bytes(b"stale-live-image", AssetKind.SOURCE, "image/png")
    use_case = CreateJobUseCase(job_repository=job_repository, job_queue=job_queue, asset_store=asset_store)
    request = RenderRequest(
        source_asset_id=asset_ref.asset_id,
        shadow=ShadowSettings(angle_deg=15),
        background=BackgroundSpec(),
        output=OutputSpec(),
    )

    first = use_case.execute(CreateJobCommand(request=request))
    assert job_queue.consume().job_id == first.job_id
    stored = job_repository.get(first.job_id)
    assert stored is not None
    stored.status = JobStatus.RUNNING
    stored.updated_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    job_repository.update(stored)

    second = use_case.execute(CreateJobCommand(request=request))

    assert second.job_id != first.job_id
    assert second.cache_status == "miss-stale-running"
    assert second.reused_existing_job is False
    assert job_queue.consume().job_id == second.job_id
