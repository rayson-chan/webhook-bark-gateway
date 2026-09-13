from typing import Any

from gateway.adapters.base import Adapter, AdapterError, first_text
from gateway.models import Notification


EVENTS = {
    "test": ("🧪 Webhook Test", "passive"),
    "nodeCreated": ("🆕 New Node", "active"),
    "nodeApproved": ("✅ Node Approved", "active"),
    "nodeAuthorized": ("✅ Node Authorized", "active"),
    "nodeNeedsApproval": ("⚠️ Node Needs Approval", "timeSensitive"),
    "nodeKeyExpiringInOneDay": ("🔑 Key Expiring Soon", "timeSensitive"),
    "nodeKeyExpired": ("❌ Node Key Expired", "timeSensitive"),
    "nodeDeleted": ("🗑️ Node Deleted", "active"),
    "userNeedsApproval": ("⚠️ User Needs Approval", "timeSensitive"),
    "userRoleUpdated": ("👤 User Role Updated", "active"),
    "policyUpdate": ("🛡️ Policy Updated", "active"),
    "subnetIPForwardingNotEnabled": ("⚠️ Subnet Routing Issue", "timeSensitive"),
    "exitNodeIPForwardingNotEnabled": ("⚠️ Exit Node Issue", "timeSensitive"),
}


class TailscaleAdapter(Adapter):
    def transform(self, payload: Any) -> list[Notification]:
        events = payload if isinstance(payload, list) else [payload]
        if not events or not all(isinstance(event, dict) for event in events):
            raise AdapterError("Tailscale payload must be an event object or array")

        notifications = []
        for event in events:
            event_type = first_text(event.get("type"), default="unknown")
            title, level = EVENTS.get(event_type, (f"🔔 {event_type}", "active"))
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            subject = first_text(
                data.get("deviceName"), data.get("nodeName"), data.get("user"), data.get("actor")
            )
            message = first_text(event.get("message"), default="Tailscale event received")
            body = "\n".join(part for part in (subject, message) if part)
            notifications.append(Notification(
                title=title,
                body=body,
                group="Tailscale",
                level=level,
                url=data.get("url"),
            ))
        return notifications

