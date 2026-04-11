from datetime import datetime, timezone

from shadowgen_contracts import ErrorInfo, JobStatus, RenderResult
from shadowgen_pipeline import PipelineContext

from shadowgen_application.ports import AssetStorePort, JobRepositoryPort, RenderPipelinePort
from shadowgen_domain import AssetNotFoundError, JobNotFoundError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessJobUseCase:
    def __init__(
        self,
        job_repository: JobRepositoryPort,
        asset_store: AssetStorePort,
        pipeline: RenderPipelinePort,
    ) -> None:
        self.job_repository = job_repository
        self.asset_store = asset_store
        self.pipeline = pipeline

    def execute(self, job_id: str):
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
            source_bytes = self.asset_store.get_bytes(job.request.source_asset_id)
            pipeline_output = self.pipeline.render(
                PipelineContext(
                    request=job.request,
                    source_image=source_bytes,
                    source_mime_type=source_ref.mime_type,
                )
            )
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
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.finished_at = utc_now()
            job.updated_at = utc_now()
            job.error = ErrorInfo(code="processing_failed", message=str(exc))
            self.job_repository.update(job)
            raise
