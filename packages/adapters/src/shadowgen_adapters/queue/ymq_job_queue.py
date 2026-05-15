from __future__ import annotations

import json

import boto3

from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class YMQQueueDelivery:
    def __init__(self, client, queue_url: str, receipt_handle: str, message: RenderJobQueuedMessage) -> None:
        self.client = client
        self.queue_url = queue_url
        self.receipt_handle = receipt_handle
        self.message = message
        self._done = False

    def ack(self) -> None:
        if self._done:
            return
        self.client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=self.receipt_handle,
        )
        self._done = True

    def nack(self) -> None:
        if self._done:
            return
        self.client.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=self.receipt_handle,
            VisibilityTimeout=0,
        )
        self._done = True

    def extend_visibility(self, timeout_sec: int) -> None:
        if self._done:
            return
        self.client.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=self.receipt_handle,
            VisibilityTimeout=timeout_sec,
        )


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
        delivery = self.receive()
        if delivery is None:
            return None
        delivery.ack()
        return delivery.message

    def receive(self) -> YMQQueueDelivery | None:
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=self.wait_time_sec,
        )
        messages = response.get("Messages", [])
        if not messages:
            return None
        raw_message = messages[0]
        return YMQQueueDelivery(
            client=self.client,
            queue_url=self.queue_url,
            receipt_handle=raw_message["ReceiptHandle"],
            message=RenderJobQueuedMessage.model_validate(json.loads(raw_message["Body"])),
        )

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
