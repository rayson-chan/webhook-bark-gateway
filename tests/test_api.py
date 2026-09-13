import os

os.environ.setdefault("BARK_DEVICE_KEY", "test-device-key")
os.environ.setdefault("GENERIC_TOKEN", "generic-test-token")

from fastapi.testclient import TestClient

from gateway.main import app


class FakeProvider:
    def __init__(self):
        self.sent = []

    async def send(self, notification):
        self.sent.append(notification)

    async def close(self):
        pass


def test_health_and_authenticated_generic_delivery():
    provider = FakeProvider()
    with TestClient(app) as client:
        app.state.provider = provider
        assert client.get("/healthz").json() == {"status": "ok"}
        response = client.post(
            "/hook/generic/",
            headers={"Authorization": "Bearer generic-test-token"},
            json={"title": "Complete", "body": "Finished", "group": "CI"},
        )
    assert response.status_code == 200
    assert response.json()["delivered"] == 1
    assert provider.sent[0].group == "CI"


def test_generic_rejects_bad_token():
    with TestClient(app) as client:
        response = client.post(
            "/hook/generic/",
            headers={"Authorization": "Bearer wrong"},
            json={"body": "Finished"},
        )
    assert response.status_code == 401
