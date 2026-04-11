from shadowgen_contracts import LocalRuntimeConfig


class MemoryRuntimeConfigStore:
    def __init__(self) -> None:
        self._config = LocalRuntimeConfig()

    def get(self) -> LocalRuntimeConfig:
        return self._config

    def update(self, config: LocalRuntimeConfig) -> LocalRuntimeConfig:
        self._config = config
        return self._config
