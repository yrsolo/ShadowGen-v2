from .http_adapter import LegacyHttpAdapter
from .stub_adapter import LegacyStubAdapter


class LegacyPipelineAdapter:
    """
    Compatibility facade so current wiring can select either live HTTP
    integration or deterministic stub behavior without leaking that choice
    into application or worker code.
    """

    def __init__(self, base_url: str | None = None, timeout_sec: float = 120.0) -> None:
        self._delegate = LegacyHttpAdapter(base_url, timeout_sec) if base_url else LegacyStubAdapter()

    def probe(self, force_refresh: bool = False):
        return self._delegate.probe(force_refresh=force_refresh)

    def submit(self, context):
        return self._delegate.submit(context)

    def poll(self, submission):
        return self._delegate.poll(submission)

    def cancel(self, submission) -> None:
        if hasattr(self._delegate, "cancel"):
            self._delegate.cancel(submission)

    def ping(self) -> bool | None:
        if hasattr(self._delegate, "ping"):
            return self._delegate.ping()
        return None
