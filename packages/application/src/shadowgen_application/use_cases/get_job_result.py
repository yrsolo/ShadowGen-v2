from shadowgen_application.ports import JobRepositoryPort
from shadowgen_domain import JobNotFoundError


class GetJobResultUseCase:
    def __init__(self, job_repository: JobRepositoryPort) -> None:
        self.job_repository = job_repository

    def execute(self, job_id: str):
        job = self.job_repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job '{job_id}' was not found.")
        return job
