from __future__ import annotations

from datetime import datetime
from hmac import compare_digest

from fastapi import Header, HTTPException, Request

from shadowgen_adapters.realtime.signing import (
    RealtimeTokenError,
    sign_job_token,
    verify_job_token as verify_signed_job_token,
)


def require_bearer_token(authorization: str | None, expected: str, label: str) -> None:
    if not expected or expected.startswith("change-me-"):
        raise HTTPException(status_code=503, detail=f"{label} token is not configured.")
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization[len(prefix) :]
    if not compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid bearer token.")


def require_internal_token(authorization: str | None = Header(default=None), expected: str = "") -> None:
    require_bearer_token(authorization=authorization, expected=expected, label="internal")


def assert_origin_allowed(request: Request, allowed_origins: list[str]) -> None:
    origin = request.headers.get("origin")
    if not origin:
        return
    if origin not in allowed_origins:
        raise HTTPException(status_code=403, detail="Origin is not allowed.")


def verify_job_token(token: str, job_id: str, secret: str, now: datetime | None = None) -> None:
    if not secret or secret.startswith("change-me-"):
        raise HTTPException(status_code=503, detail="Realtime signing secret is not configured.")
    try:
        verify_signed_job_token(token=token, job_id=job_id, secret=secret, now=now)
    except RealtimeTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid realtime token.")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid realtime token.") from exc
