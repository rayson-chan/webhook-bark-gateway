# Webhook Bark Gateway

[简体中文](README.zh-CN.md) | English

A lightweight, extensible gateway that converts service-specific webhooks into clean [Bark](https://github.com/Finb/bark-server) notifications. It runs separately from `bark-server`, exposes `/hook/<service>/`, and reaches Bark on the Docker host.

> Status: early release (`v0.1.x`). The core flow is tested; real Paseo payloads and production Linux deployments should receive additional field testing.

## Features

- Docker Compose, non-root container, and health check
- Tailscale, Paseo, and Generic adapters
- Provider abstraction, with Bark implemented first
- Normalized `group`, `title`, `body`, `level`, and `url`
- Independent credentials per source
- Native Tailscale HMAC-SHA256 verification and replay-window protection
- Batched Tailscale events and safe fallback for new event types
- Structured JSON logs, request IDs, payload limits, and explicit errors
- No database and no modification to the existing Bark server

## Why a separate project?

The closest projects solve adjacent problems: [Bark Notice App](https://github.com/Ballen2270/Bark-Notice-App) adds a full UI and requires MySQL/Redis; [Webhook Relay](https://github.com/webhookrelay) is a broader forwarding platform; [Apprise](https://github.com/caronc/apprise) is an excellent multi-provider layer but not a source-aware adapter gateway; and [bark-web](https://github.com/space4yyy/bark-web) is an interactive sender. None is a small fork away from this exact authentication and event-formatting model.

## Architecture

```text
POST /hook/<service>/
  → per-source token or native signature
  → adapter: tailscale | paseo | generic
  → Notification(group, title, body, level, url)
  → provider: Bark
  → http://host.docker.internal:8080/push
```

Endpoints are `POST /hook/tailscale/`, `/hook/paseo/`, `/hook/generic/`, and `GET /healthz`.

## Quick start

```bash
cp .env.example .env
```

Set `BARK_DEVICE_KEY`, plus distinct `PASEO_TOKEN` and `GENERIC_TOKEN` values. For Tailscale, configure the native secret shown when the webhook is created:

```dotenv
TAILSCALE_WEBHOOK_SECRET=your-tailscale-webhook-secret
```

If native signing is unavailable, leave it blank and use `TAILSCALE_TOKEN` instead. Then start:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f webhook-bark-gateway
```

The gateway binds host `127.0.0.1:8787`. Its default `BARK_BASE_URL=http://host.docker.internal:8080` reaches Bark through Docker's host gateway, allowing Bark to remain bound to host `127.0.0.1:8080`.

## Generic request

```bash
curl -X POST 'http://127.0.0.1:8787/hook/generic/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_GENERIC_TOKEN' \
  -d '{"group":"Backup","title":"✅ Backup Complete","body":"nas-01\nSnapshot completed","level":"active","url":"https://example.com/jobs/42"}'
```

Tokens may use `Authorization: Bearer ...`, `X-Webhook-Token`, or fallback `?token=`. Prefer headers because URLs are commonly stored in access logs. Generic `body` may also be named `message` or `text`; `level` must be `active`, `timeSensitive`, or `passive`.

## Tailscale and Paseo

Tailscale accepts the native JSON event array. It formats common device, key, user, policy, and routing events; unknown types still produce notifications. Set the Tailscale destination to `None` and use `https://notify.example.com/hooks/tailscale/`.

Paseo tolerates top-level or nested `data` fields. Recommended payload:

```json
{"event":"completed","data":{"project":"SouthGrid","agentName":"GPT Expert","summary":"Task completed","url":"https://paseo.example/agents/123"}}
```

Known states include completed, success, failed, error, needs-attention, waiting, started, and running. Namespaced events such as `agent.completed` are accepted.

## Nginx and migration

```nginx
location /hooks/ {
    proxy_pass http://127.0.0.1:8787/hook/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
    client_max_body_size 1m;
    proxy_connect_timeout 5s;
    proxy_read_timeout 15s;
}
```

The trailing slashes map `/hooks/tailscale/` to `/hook/tailscale/`. During migration, proxy legacy paths directly instead of redirecting them:

```nginx
location = /tailscale-hook/ { proxy_pass http://127.0.0.1:8787/hook/tailscale/; }
location = /paseo-hook/ { proxy_pass http://127.0.0.1:8787/hook/paseo/; }
```

Some senders do not preserve POST bodies or authorization headers across redirects. Remove compatibility locations only after their access logs stay quiet.

## Extending and operating

To add GitHub, PVE, or Training, implement `Adapter.transform()`, register the adapter, add an independent credential or native signature verifier, and add tests. Nginx remains unchanged. New outputs implement the provider interface.

Logs are one-line JSON and exclude credentials and raw payloads. Responses use `401` for authentication, `404` for unknown adapters, `413` for oversized payloads, `422` for invalid payloads, `502` for Bark failures, and `503` for missing source configuration. Delivery is synchronous and has no persistent retry queue; a partially delivered Tailscale batch may be retried and produce duplicates.

## Development, license, and security

```bash
python -m pip install -r requirements-dev.txt
pytest
python -m compileall -q gateway
docker build -t webhook-bark-gateway:dev .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Released under the [MIT License](LICENSE). This is an independent community project and is not affiliated with or endorsed by Bark, Tailscale, Paseo, or their owners.

