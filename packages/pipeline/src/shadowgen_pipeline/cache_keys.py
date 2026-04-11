import hashlib

from shadowgen_contracts import RenderRequest


def source_image_key(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def render_request_key(source_hash: str, request: RenderRequest) -> str:
    payload = f"{source_hash}:{request.model_dump_json(sort_keys=True)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
