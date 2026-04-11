from shadowgen_contracts import QueueDiagnostics, RenderJobQueuedMessage


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._items: list[RenderJobQueuedMessage] = []

    def publish(self, message: RenderJobQueuedMessage) -> None:
        self._items.append(message)

    def consume(self) -> RenderJobQueuedMessage | None:
        if not self._items:
            return None
        return self._items.pop(0)

    def diagnostics(self) -> QueueDiagnostics:
        return QueueDiagnostics(
            backend="memory",
            queued_count=len(self._items),
            in_flight_count=0,
            notes=["In-memory queue is active."],
        )

    def clear(self) -> None:
        self._items.clear()
