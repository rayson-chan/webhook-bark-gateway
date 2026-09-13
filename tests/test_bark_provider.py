import json

import httpx
import pytest

from gateway.models import Notification
from gateway.providers.bark import BarkProvider


@pytest.mark.asyncio
async def test_official_bark_v2_endpoint_and_payload():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.day.app/push"
        payload = json.loads(request.content)
        assert payload["device_key"] == "device-key"
        assert payload["title"] == "Complete"
        return httpx.Response(200, json={"code": 200, "message": "success"})

    provider = BarkProvider("https://api.day.app", "device-key")
    await provider._client.aclose()
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        await provider.send(Notification(title="Complete", body="Done", group="CI"))
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_exact_push_url_supports_reverse_proxy_subpath():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://notify.example.com/bark-api/v2/push"
        return httpx.Response(200, json={"code": 200})

    provider = BarkProvider(
        "https://ignored.example.com",
        "device-key",
        push_url="https://notify.example.com/bark-api/v2/push",
    )
    await provider._client.aclose()
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        await provider.send(Notification(title="Complete", body="Done", group="CI"))
    finally:
        await provider.close()
