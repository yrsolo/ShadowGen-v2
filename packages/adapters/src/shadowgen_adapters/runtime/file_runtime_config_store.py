from __future__ import annotations

from pathlib import Path

from shadowgen_contracts import LocalRuntimeConfig


class FileRuntimeConfigStore:
    def __init__(self, state_dir: str | Path) -> None:
        self.path = Path(state_dir) / "system" / "runtime-config.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self) -> LocalRuntimeConfig:
        if not self.path.exists():
            return LocalRuntimeConfig()
        return LocalRuntimeConfig.model_validate_json(self.path.read_text(encoding="utf-8"))

    def update(self, config: LocalRuntimeConfig) -> LocalRuntimeConfig:
        self.path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return config
