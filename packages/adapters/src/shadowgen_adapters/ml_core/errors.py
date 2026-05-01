from shadowgen_contracts import ErrorInfo


class MLCoreTransportError(RuntimeError):
    pass


class MLCoreRetryableError(MLCoreTransportError):
    pass


class MLCoreNonRetryableError(MLCoreTransportError):
    pass


class MLCoreAsyncJobFailedError(RuntimeError):
    def __init__(self, error: ErrorInfo) -> None:
        self.error = error
        super().__init__(error.message)
