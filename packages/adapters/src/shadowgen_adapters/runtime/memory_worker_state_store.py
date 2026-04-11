from shadowgen_contracts import WorkerRuntimeState


class MemoryWorkerStateStore:
    def __init__(self) -> None:
        self._state = WorkerRuntimeState()

    def get(self) -> WorkerRuntimeState:
        return self._state

    def update(self, state: WorkerRuntimeState) -> WorkerRuntimeState:
        self._state = state
        return self._state
