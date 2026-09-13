import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException

from gateway.security import _verify_tailscale_signature


def test_tailscale_signature_accepts_valid_payload():
    body = b'[{"type":"test"}]'
    timestamp = int(time.time())
    digest = hmac.new(b"secret", str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
    _verify_tailscale_signature(f"t={timestamp},v1={digest}", body, "secret", 300)


def test_tailscale_signature_rejects_tampering():
    timestamp = int(time.time())
    with pytest.raises(HTTPException) as error:
        _verify_tailscale_signature(f"t={timestamp},v1={'0' * 64}", b"[]", "secret", 300)
    assert error.value.status_code == 401


def test_tailscale_signature_rejects_replay():
    timestamp = int(time.time()) - 301
    with pytest.raises(HTTPException) as error:
        _verify_tailscale_signature(f"t={timestamp},v1={'0' * 64}", b"[]", "secret", 300)
    assert "outside tolerance" in error.value.detail
