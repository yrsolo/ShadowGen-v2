from __future__ import annotations

from pathlib import Path

from shadowgen_contracts import WorkerRuntimeState


class FileWorkerStateStore:
    def __init__(self, state_dir: str | Path) -> None:
        self.path = Path(state_dir) / "system" / "worker-state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self) -> WorkerRuntimeState:
        if not self.path.exists():
            return WorkerRuntimeState()
        return WorkerRuntimeState.model_validate_json(self.path.read_text(encoding="utf-8"))

    def update(self, state: WorkerRuntimeState) -> WorkerRuntimeState:
        self.path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        return state
