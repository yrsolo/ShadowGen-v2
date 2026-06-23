from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from hmac import compare_digest


class RealtimeTokenError(ValueError):
    pass


def sign_job_token(job_id: str, expires_at: datetime, secret: str) -> str:
    payload = {
        "job_id": job_id,
        "exp": int(expires_at.timestamp()),
    }
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_part = _b64encode(payload_bytes)
    signature = hmac.new(secret.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def verify_job_token(token: str, job_id: str, secret: str, now: datetime | None = None) -> None:
    parts = token.split(".")
    if len(parts) != 2:
        raise RealtimeTokenError("Invalid realtime token.")
    payload_part, signature_part = parts
    expected_signature = hmac.new(secret.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).digest()
    if not compare_digest(_b64encode(expected_signature), signature_part):
        raise RealtimeTokenError("Invalid realtime token.")
    try:
        payload = json.loads(_b64decode(payload_part).decode("utf-8"))
    except Exception as exc:
        raise RealtimeTokenError("Invalid realtime token.") from exc
    if payload.get("job_id") != job_id:
        raise RealtimeTokenError("Realtime token does not match this job.")
    current = now or datetime.now(timezone.utc)
    if int(payload.get("exp", 0)) < int(current.timestamp()):
        raise RealtimeTokenError("Realtime token expired.")


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
