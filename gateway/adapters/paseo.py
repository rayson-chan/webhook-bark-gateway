from typing import Any

from gateway.adapters.base import Adapter, AdapterError, first_text
from gateway.models import Notification


STATUS_STYLE = {
    "completed": ("✅ Agent Completed", "active"),
    "success": ("✅ Agent Completed", "active"),
    "failed": ("❌ Agent Failed", "timeSensitive"),
    "error": ("❌ Agent Failed", "timeSensitive"),
    "needs_attention": ("⚠️ Agent Needs Attention", "timeSensitive"),
    "waiting": ("⏳ Agent Waiting", "active"),
    "started": ("🚀 Agent Started", "passive"),
    "running": ("▶️ Agent Running", "passive"),
}


class PaseoAdapter(Adapter):
    """Tolerant adapter because Paseo event schemas may vary by integration."""

    def transform(self, payload: Any) -> list[Notification]:
        if not isinstance(payload, dict):
            raise AdapterError("Paseo payload must be a JSON object")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        status = first_text(
            data.get("status"), payload.get("status"), payload.get("event"), payload.get("type"),
            default="event",
        ).lower().replace("-", "_").replace(" ", "_")
        # Accept namespaced event names such as "agent.completed".
        status = status.rsplit(".", 1)[-1]
        title, level = STATUS_STYLE.get(status, (f"🔔 {status.replace('_', ' ').title()}", "active"))
        agent = first_text(data.get("agentName"), data.get("agent"), data.get("name"), data.get("id"))
        project = first_text(data.get("project"), data.get("workspace"), data.get("cwd"))
        summary = first_text(data.get("summary"), data.get("message"), payload.get("message"), default="Paseo event received")
        heading = " · ".join(part for part in (project, agent) if part)
        body = "\n".join(part for part in (heading, summary) if part)
        return [Notification(
            title=title,
            body=body,
            group="Paseo",
            level=level,
            url=data.get("url") or payload.get("url"),
        )]
