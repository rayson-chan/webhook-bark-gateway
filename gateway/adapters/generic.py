from typing import Any

from gateway.adapters.base import Adapter, AdapterError, first_text
from gateway.models import Notification


class GenericAdapter(Adapter):
    def transform(self, payload: Any) -> list[Notification]:
        if not isinstance(payload, dict):
            raise AdapterError("Generic payload must be a JSON object")
        title = first_text(payload.get("title"), payload.get("event"), default="Webhook Event")
        body = first_text(payload.get("body"), payload.get("message"), payload.get("text"))
        if not body:
            raise AdapterError("Generic payload requires body, message, or text")
        return [Notification(
            title=title,
            body=body,
            group=first_text(payload.get("group"), payload.get("source"), default="Webhook"),
            level=payload.get("level", "active"),
            url=payload.get("url"),
        )]

