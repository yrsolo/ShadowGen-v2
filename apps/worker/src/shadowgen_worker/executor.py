class JobExecutor:
    def __init__(self, process_job_use_case_factory) -> None:
        self.process_job_use_case_factory = process_job_use_case_factory

    def execute(self, job_id: str):
        return self.process_job_use_case_factory().execute(job_id)
