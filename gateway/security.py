import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status

from gateway.config import Settings


def _supplied_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return request.headers.get("x-webhook-token", "") or request.query_params.get("token", "")


def verify_source_auth(service: str, request: Request, raw_body: bytes, settings: Settings) -> None:
    if service == "tailscale" and settings.tailscale_webhook_secret:
        _verify_tailscale_signature(
            request.headers.get("tailscale-webhook-signature", ""),
            raw_body,
            settings.tailscale_webhook_secret,
            settings.tailscale_signature_tolerance_seconds,
        )
        return

    expected = settings.token_for(service)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Authentication is not configured for service '{service}'",
        )
    if not hmac.compare_digest(_supplied_token(request), expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook credential")


def _verify_tailscale_signature(header: str, raw_body: bytes, secret: str, tolerance: int) -> None:
    try:
        values = dict(part.strip().split("=", 1) for part in header.split(",") if "=" in part)
        timestamp = int(values["t"])
        supplied = values["v1"]
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Missing or malformed Tailscale signature") from None

    if abs(int(time.time()) - timestamp) > tolerance:
        raise HTTPException(status_code=401, detail="Tailscale signature timestamp is outside tolerance")

    signed = str(timestamp).encode() + b"." + raw_body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid Tailscale signature")

