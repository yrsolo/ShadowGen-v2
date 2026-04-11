from shadowgen_application.ports import RuntimeConfigStorePort


class GetRuntimeConfigUseCase:
    def __init__(self, runtime_config_store: RuntimeConfigStorePort) -> None:
        self.runtime_config_store = runtime_config_store

    def execute(self):
        return self.runtime_config_store.get()
