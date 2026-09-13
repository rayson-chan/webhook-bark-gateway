import httpx

from gateway.models import Notification
from gateway.providers.base import Provider, ProviderError


class BarkProvider(Provider):
    def __init__(self, base_url: str, device_key: str, timeout: float = 10) -> None:
        endpoint = f"{base_url.rstrip('/')}/push"
        self._endpoint = endpoint
        self._device_key = device_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def send(self, notification: Notification) -> None:
        payload = notification.model_dump(mode="json", exclude_none=True)
        payload["device_key"] = self._device_key
        try:
            response = await self._client.post(self._endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Bark request failed: {exc}") from exc
        if result.get("code") != 200:
            raise ProviderError(f"Bark rejected notification: {result.get('message', 'unknown error')}")
