from shadowgen_adapters.legacy_pipeline.mapper import map_render_request_to_legacy_payload
from shadowgen_contracts import RenderRequest


def test_legacy_mapper_keeps_v2_request_internal() -> None:
    payload = map_render_request_to_legacy_payload(RenderRequest(source_asset_id="asset-1"))

    assert payload["rot"] == "45"
    assert payload["return_debug"] == "false"
    assert payload["max_objects"] == "1"
    assert "source_asset_id" not in payload
    assert "elevation_deg" not in payload
    assert "pipeline_version" not in payload
