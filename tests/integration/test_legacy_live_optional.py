import os

import pytest

from shadowgen_adapters.legacy_pipeline.http_adapter import LegacyHttpAdapter


@pytest.mark.skipif(
    not os.getenv("LEGACY_ML_LIVE_TEST_URL"),
    reason="LEGACY_ML_LIVE_TEST_URL is not configured",
)
def test_legacy_live_server_ping() -> None:
    adapter = LegacyHttpAdapter(os.environ["LEGACY_ML_LIVE_TEST_URL"], timeout_sec=5.0)
    assert adapter.ping() is True
