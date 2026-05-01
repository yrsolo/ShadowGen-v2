from uuid import uuid4

from shadowgen_contracts import JobRecord, JobStatus, RenderJobQueuedMessage
from shadowgen_pipeline.cache_keys import render_request_key

from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.ports import AssetStorePort, JobQueuePublisherPort, JobRepositoryPort


class CreateJobUseCase:
    def __init__(
        self,
        job_repository: JobRepositoryPort,
        job_queue: JobQueuePublisherPort,
        asset_store: AssetStorePort,
    ) -> None:
        self.job_repository = job_repository
        self.job_queue = job_queue
        self.asset_store = asset_store

    def execute(self, command: CreateJobCommand) -> JobRecord:
        request_cache_key = render_request_key(
            source_hash=command.source_hash or self.asset_store.get_source_hash(command.request.source_asset_id),
            request=command.request,
        )
        cached = self.job_repository.find_by_request_cache_key(request_cache_key)
        if cached is not None and cached.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.SUCCEEDED}:
            return cached

        job = JobRecord(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            request=command.request,
            request_cache_key=request_cache_key,
        )
        self.job_repository.create(job)
        self.job_queue.publish(RenderJobQueuedMessage(job_id=job.job_id))
        return job
