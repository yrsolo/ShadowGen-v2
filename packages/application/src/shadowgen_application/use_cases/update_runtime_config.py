from shadowgen_application.ports import RuntimeConfigStorePort
from shadowgen_contracts import LocalRuntimeConfig


class UpdateRuntimeConfigUseCase:
    def __init__(self, runtime_config_store: RuntimeConfigStorePort) -> None:
        self.runtime_config_store = runtime_config_store

    def execute(self, config: LocalRuntimeConfig):
        return self.runtime_config_store.update(config)
