import time


class WorkerLoop:
    def __init__(self, queue, executor, state_service, poll_interval_sec: float = 1.0) -> None:
        self.queue = queue
        self.executor = executor
        self.state_service = state_service
        self.poll_interval_sec = poll_interval_sec

    def tick(self) -> bool:
        message = self.queue.consume()
        if message is None:
            self.state_service.heartbeat_idle()
            return False
        self.state_service.job_started(message.job_id)
        try:
            job = self.executor.execute(message.job_id)
            self.state_service.job_finished(job)
        except Exception as exc:
            self.state_service.job_failed(message.job_id, str(exc))
        return True

    def run_forever(self):
        self.state_service.boot()
        while True:
            if not self.tick():
                time.sleep(self.poll_interval_sec)
