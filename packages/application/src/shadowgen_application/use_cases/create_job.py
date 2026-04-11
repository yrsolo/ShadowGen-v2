from uuid import uuid4

from shadowgen_contracts import JobRecord, JobStatus, RenderJobQueuedMessage

from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.ports import JobQueuePublisherPort, JobRepositoryPort


class CreateJobUseCase:
    def __init__(self, job_repository: JobRepositoryPort, job_queue: JobQueuePublisherPort) -> None:
        self.job_repository = job_repository
        self.job_queue = job_queue

    def execute(self, command: CreateJobCommand) -> JobRecord:
        job = JobRecord(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            request=command.request,
        )
        self.job_repository.create(job)
        self.job_queue.publish(RenderJobQueuedMessage(job_id=job.job_id))
        return job
