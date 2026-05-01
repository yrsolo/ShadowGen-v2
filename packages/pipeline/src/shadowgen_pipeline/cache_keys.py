import hashlib
import json

from shadowgen_contracts import RenderRequest


def source_image_key(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def render_request_key(source_hash: str, request: RenderRequest) -> str:
    normalized = request.model_copy(deep=True)
    normalized.source_asset_id = "__normalized_source__"
    normalized_json = json.dumps(
        normalized.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = f"{source_hash}:{normalized_json}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
