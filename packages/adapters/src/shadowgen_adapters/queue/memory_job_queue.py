from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class MemoryQueueDelivery:
    def __init__(self, queue: "InMemoryJobQueue", message: RenderJobQueuedMessage) -> None:
        self.queue = queue
        self.message = message
        self._done = False

    def ack(self) -> None:
        self._done = True

    def nack(self) -> None:
        if self._done:
            return
        self.queue._items.insert(0, self.message)
        self._done = True

    def extend_visibility(self, timeout_sec: int) -> None:
        _ = timeout_sec


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._items: list[RenderJobQueuedMessage] = []

    def publish(self, message: RenderJobQueuedMessage) -> None:
        self._items.append(message)

    def consume(self) -> RenderJobQueuedMessage | None:
        delivery = self.receive()
        if delivery is None:
            return None
        delivery.ack()
        return delivery.message

    def receive(self) -> MemoryQueueDelivery | None:
        if not self._items:
            return None
        return MemoryQueueDelivery(self, self._items.pop(0))

    def diagnostics(self) -> QueueDiagnostics:
        return QueueDiagnostics(
            backend="memory",
            queued_count=len(self._items),
            in_flight_count=0,
            notes=["In-memory queue is active."],
        )

    def clear(self) -> None:
        self._items.clear()
