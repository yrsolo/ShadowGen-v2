from pathlib import Path

from shadowgen_adapters.legacy_pipeline.stub_adapter import LegacyStubAdapter
from shadowgen_adapters.runtime.factories import build_runtime_adapters
from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase
from shadowgen_application.use_cases.process_job import ProcessJobUseCase
from shadowgen_contracts import AssetKind, RenderRequest


def test_file_backed_runtime_supports_separate_instances(tmp_path: Path) -> None:
    api_runtime = build_runtime_adapters(state_backend="file", queue_backend="file", state_dir=str(tmp_path))
    worker_runtime = build_runtime_adapters(state_backend="file", queue_backend="file", state_dir=str(tmp_path))

    asset_ref = api_runtime.asset_store.put_bytes(b"image-bytes", AssetKind.SOURCE, "image/png")
    create_use_case = CreateJobUseCase(job_repository=api_runtime.job_repository, job_queue=api_runtime.job_queue)
    created = create_use_case.execute(CreateJobCommand(request=RenderRequest(source_asset_id=asset_ref.asset_id)))

    message = worker_runtime.job_queue.consume()
    assert message is not None
    assert message.job_id == created.job_id

    process_use_case = ProcessJobUseCase(
        job_repository=worker_runtime.job_repository,
        asset_store=worker_runtime.asset_store,
        pipeline=LegacyStubAdapter(),
    )
    process_use_case.execute(created.job_id)

    get_job = GetJobUseCase(job_repository=api_runtime.job_repository)
    stored = get_job.execute(created.job_id)
    assert stored.status == "succeeded"
