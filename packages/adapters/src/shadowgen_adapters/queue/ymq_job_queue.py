from __future__ import annotations

import json

import boto3

from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class YMQJobQueue:
    def __init__(
        self,
        queue_url: str,
        endpoint_url: str,
        region_name: str,
        access_key_id: str,
        secret_access_key: str,
        wait_time_sec: int = 2,
    ) -> None:
        self.queue_url = queue_url
        self.wait_time_sec = wait_time_sec
        self.client = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def publish(self, message: RenderJobQueuedMessage) -> None:
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message.model_dump_json(),
        )

    def consume(self) -> RenderJobQueuedMessage | None:
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=self.wait_time_sec,
        )
        messages = response.get("Messages", [])
        if not messages:
            return None
        raw_message = messages[0]
        self.client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=raw_message["ReceiptHandle"],
        )
        return RenderJobQueuedMessage.model_validate(json.loads(raw_message["Body"]))

    def diagnostics(self) -> QueueDiagnostics:
        try:
            attributes = self.client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"],
            )["Attributes"]
            return QueueDiagnostics(
                backend="ymq",
                queued_count=int(attributes.get("ApproximateNumberOfMessages", 0)),
                in_flight_count=int(attributes.get("ApproximateNumberOfMessagesNotVisible", 0)),
                notes=[f"Queue URL: {self.queue_url}"],
            )
        except Exception as exc:
            return QueueDiagnostics(
                backend="ymq",
                queued_count=None,
                in_flight_count=None,
                notes=[f"Queue diagnostics failed: {exc}"],
            )
