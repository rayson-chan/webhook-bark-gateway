# Webhook Bark Gateway

简体中文 | [English](README.md)

一个轻量、可扩展的 `Webhook → 标准通知 → Bark` 网关。它独立于现有 `bark-server` 运行，通过统一 `/hook/<service>/` 接收事件，再访问 Docker 宿主机上的 Bark。

> 状态：早期版本（`v0.1.x`）。核心流程已有测试；真实 Paseo 载荷和生产 Linux 环境仍建议进一步验证。

## 功能

- Docker Compose、非 root 容器和健康检查
- Tailscale、Paseo、Generic adapter，以及可扩展 provider
- 统一 `group`、`title`、`body`、`level`、`url`
- 每个来源使用独立凭据
- Tailscale 原生 HMAC-SHA256 签名校验、重放时间窗和批量事件
- JSON 结构化日志、request ID、大小限制和明确错误响应
- 不需要数据库，也不修改现有 Bark 服务

## 取舍结论

[Bark Notice App](https://github.com/Ballen2270/Bark-Notice-App) 带完整 UI 并依赖 MySQL/Redis；[Webhook Relay](https://github.com/webhookrelay) 是更大的转发平台；[Apprise](https://github.com/caronc/apprise) 适合未来作为多渠道 provider，但不是来源感知的 adapter 网关；[bark-web](https://github.com/space4yyy/bark-web) 是人工发送界面。它们都不能通过小幅 fork 同时满足本项目的认证与事件文案需求。

## 架构与入口

```text
POST /hook/<service>/
  → 来源独立 token / 原生签名
  → adapter: tailscale | paseo | generic
  → Notification(group, title, body, level, url)
  → provider: Bark
  → http://host.docker.internal:8080/push
```

入口为 `POST /hook/tailscale/`、`/hook/paseo/`、`/hook/generic/` 和 `GET /healthz`。

## 快速部署

```bash
cp .env.example .env
```

填写 `BARK_DEVICE_KEY`，并为 `PASEO_TOKEN`、`GENERIC_TOKEN` 设置不同的长随机值。Tailscale 推荐使用创建 webhook 时显示的原生 secret：

```dotenv
TAILSCALE_WEBHOOK_SECRET=你的Tailscale-webhook-secret
```

无法使用原生签名时，可留空并配置 `TAILSCALE_TOKEN`。启动：

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f webhook-bark-gateway
```

网关只发布到宿主机 `127.0.0.1:8787`。默认 `BARK_BASE_URL=http://host.docker.internal:8080` 通过 Docker host gateway 访问 Bark，因此 Bark 可以继续只监听宿主机 `127.0.0.1:8080`。

## Generic 示例

```bash
curl -X POST 'http://127.0.0.1:8787/hook/generic/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer 你的GENERIC_TOKEN' \
  -d '{"group":"Backup","title":"✅ Backup Complete","body":"nas-01\nSnapshot completed","level":"active","url":"https://example.com/jobs/42"}'
```

Token 支持 `Authorization: Bearer ...`、`X-Webhook-Token` 或兼容用的 `?token=`。URL 常被日志记录，因此推荐请求头。`body` 也可写成 `message` 或 `text`；`level` 仅允许 `active`、`timeSensitive`、`passive`。

## Tailscale 与 Paseo

Tailscale adapter 接收官方 JSON 数组，支持节点、密钥、用户、策略和路由事件；未知新事件也会发送。控制台 Destination 选择 `None`，URL 使用 `https://notify.example.com/hooks/tailscale/`。

Paseo adapter 会宽容读取顶层或 `data` 字段，推荐：

```json
{"event":"completed","data":{"project":"SouthGrid","agentName":"GPT Expert","summary":"任务执行完成","url":"https://paseo.example/agents/123"}}
```

支持 completed、success、failed、error、needs-attention、waiting、started、running，以及 `agent.completed` 这类命名空间事件。

## Nginx 与迁移

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

两个尾部 `/` 会把 `/hooks/tailscale/` 映射为 `/hook/tailscale/`。迁移期直接代理旧路径，不要跳转：

```nginx
location = /tailscale-hook/ { proxy_pass http://127.0.0.1:8787/hook/tailscale/; }
location = /paseo-hook/ { proxy_pass http://127.0.0.1:8787/hook/paseo/; }
```

部分发送方不会跨跳转保留 POST body 或认证头。确认旧路径长期没有访问后，再删除兼容配置。

## 扩展、运维与开发

新增 GitHub、PVE 或 Training 时，实现 `Adapter.transform()`、注册 adapter、添加独立凭据或原生签名校验，并补测试；Nginx 无需修改。新增输出渠道时实现 provider。

日志为单行 JSON，不记录凭据或原始 payload。`401` 表示认证错误、`404` 未知 adapter、`413` 请求过大、`422` 载荷错误、`502` Bark 投递失败、`503` 来源未配置认证。当前是同步投递且没有持久化队列；Tailscale 批次部分成功后重投可能重复。

```bash
python -m pip install -r requirements-dev.txt
pytest
python -m compileall -q gateway
docker build -t webhook-bark-gateway:dev .
```

另见 [贡献指南](CONTRIBUTING.md) 和 [安全策略](SECURITY.md)。项目采用 [MIT License](LICENSE)，是独立社区项目，不代表 Bark、Tailscale 或 Paseo 官方。

