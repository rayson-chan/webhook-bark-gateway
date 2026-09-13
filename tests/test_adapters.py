from gateway.adapters.generic import GenericAdapter
from gateway.adapters.paseo import PaseoAdapter
from gateway.adapters.tailscale import TailscaleAdapter


def test_generic_normalizes_notification():
    result = GenericAdapter().transform({"title": "Build", "message": "Done", "group": "CI"})
    assert result[0].model_dump(exclude_none=True) == {
        "title": "Build", "body": "Done", "group": "CI", "level": "active"
    }


def test_tailscale_handles_batch_and_device():
    result = TailscaleAdapter().transform([{
        "type": "nodeKeyExpired",
        "message": "Node key expired",
        "data": {"deviceName": "server-1", "url": "https://login.tailscale.com/admin/machines/1"},
    }])
    assert result[0].title == "❌ Node Key Expired"
    assert result[0].body == "server-1\nNode key expired"
    assert result[0].level == "timeSensitive"


def test_paseo_accepts_tolerant_shape():
    result = PaseoAdapter().transform({
        "event": "completed",
        "data": {"project": "SouthGrid", "agentName": "GPT Expert", "summary": "任务执行完成"},
    })
    assert result[0].title == "✅ Agent Completed"
    assert result[0].body == "SouthGrid · GPT Expert\n任务执行完成"

