from shadowgen_contracts import RenderRequest


def map_render_request_to_legacy_payload(request: RenderRequest) -> dict[str, str]:
    # Legacy ShadowGEN parses rot with int(v), so "45.0" falls back to 0.
    legacy_rot = str(int(round(request.shadow.angle_deg)))
    return {
        "rot": legacy_rot,
        "return_debug": str(request.output.return_debug).lower(),
        "max_objects": "1",
    }
