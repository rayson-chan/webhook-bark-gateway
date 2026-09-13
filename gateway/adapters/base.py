from abc import ABC, abstractmethod
from typing import Any

from gateway.models import Notification


class AdapterError(ValueError):
    pass


class Adapter(ABC):
    @abstractmethod
    def transform(self, payload: Any) -> list[Notification]:
        raise NotImplementedError


def first_text(*values: Any, default: str = "") -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default

