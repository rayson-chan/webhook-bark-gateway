from abc import ABC, abstractmethod

from gateway.models import Notification


class ProviderError(RuntimeError):
    pass


class Provider(ABC):
    @abstractmethod
    async def send(self, notification: Notification) -> None:
        raise NotImplementedError

