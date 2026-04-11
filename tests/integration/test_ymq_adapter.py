from shadowgen_adapters.queue.ymq_job_queue import YMQJobQueue
from shadowgen_contracts import RenderJobQueuedMessage


class FakeSqsClient:
    def __init__(self) -> None:
        self.sent_messages = []

    def send_message(self, **kwargs):
        self.sent_messages.append(kwargs)

    def receive_message(self, **kwargs):
        return {
            "Messages": [
                {
                    "Body": '{"message_version":"1","job_id":"job-1","routing_key":"render.job.queued"}',
                    "ReceiptHandle": "handle-1",
                }
            ]
        }

    def delete_message(self, **kwargs):
        self.deleted = kwargs

    def get_queue_attributes(self, **kwargs):
        return {
            "Attributes": {
                "ApproximateNumberOfMessages": "3",
                "ApproximateNumberOfMessagesNotVisible": "1",
            }
        }


def test_ymq_adapter_contract(monkeypatch) -> None:
    fake_client = FakeSqsClient()
    monkeypatch.setattr("shadowgen_adapters.queue.ymq_job_queue.boto3.client", lambda *args, **kwargs: fake_client)

    queue = YMQJobQueue(
        queue_url="https://example.queue",
        endpoint_url="https://message-queue.api.cloud.yandex.net",
        region_name="ru-central1",
        access_key_id="key",
        secret_access_key="secret",
    )

    queue.publish(RenderJobQueuedMessage(job_id="job-1"))
    message = queue.consume()
    diagnostics = queue.diagnostics()

    assert fake_client.sent_messages
    assert message is not None
    assert message.job_id == "job-1"
    assert diagnostics.backend == "ymq"
    assert diagnostics.queued_count == 3
