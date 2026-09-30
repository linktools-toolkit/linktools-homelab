# Push MCP

基于 [push-all-in-one](https://github.com/CaoMeiYouRen/push-all-in-one) 的推送 MCP 服务。提供 Streamable HTTP `/mcp`，支持多个客户端并发调用，通过 Nginx 暴露。服务端和直连端口均校验 Bearer Token。

## 部署与配置

镜像由 `.github/workflows/build-mcp-push.yml` 构建并发布到 `ghcr.io/linktools-toolkit/mcp-push`。首次部署前需先发布镜像。Workflow 支持手动指定上游 npm 版本、强制重建、每日检查更新，以及镜像源文件推送到 `master` 时重建；发布前用本机模拟渠道检查 MCP，不发送真实通知。

例如配置企业微信群机器人：

```bash
ct-cntr config set mcp-push MCP_PUSH_WECHAT_ROBOT_KEY=你的机器人Key
ct-cntr up mcp-push
ct-cntr exec mcp-push token
```

将输出的 Token 填入 MCP 客户端：

```json
{
  "mcpServers": {
    "push": {
      "url": "https://<MCP_PUSH_DOMAIN>/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_PUSH_TOKEN>"
      }
    }
  }
}
```

`MCP_PUSH_DOMAIN` 默认由框架分配。`MCP_PUSH_TOKEN` 首次自动生成并缓存，也可自行设置至少 32 位、不含空白的字符串。`MCP_PUSH_TAG` 默认为 `latest`，可指定上游版本标签（例如 `4.5.4`）。`MCP_PUSH_PORT` 默认为 `0`；设为非零后可通过 `http://<主机IP>:<端口>/mcp` 访问，同样需要 Token。容器网络内地址为 `http://mcp-push:8931/mcp`。

## 渠道参数

在上游配置字段前加 `MCP_PUSH_`，通过 `ct-cntr config set mcp-push KEY=VALUE` 设置。`extend_configs` 发现这些扩展项，由 Compose 按原名注入；服务端依据上游 schema 读取、转换数字类型并应用默认值。凭据由服务端保存，不作为 MCP 调用参数传递。

| MCP 渠道名 | 常用配置 |
| --- | --- |
| `WechatRobot` | `MCP_PUSH_WECHAT_ROBOT_KEY` |
| `WechatApp` | `MCP_PUSH_WECHAT_APP_CORPID`、`MCP_PUSH_WECHAT_APP_SECRET`、`MCP_PUSH_WECHAT_APP_AGENTID` |
| `Dingtalk` | `MCP_PUSH_DINGTALK_ACCESS_TOKEN`、可选 `MCP_PUSH_DINGTALK_SECRET` |
| `Feishu` | `MCP_PUSH_FEISHU_APP_ID`、`MCP_PUSH_FEISHU_APP_SECRET` |
| `Telegram` | `MCP_PUSH_TELEGRAM_BOT_TOKEN`、`MCP_PUSH_TELEGRAM_CHAT_ID` |
| `CustomEmail` | `MCP_PUSH_EMAIL_HOST`、`MCP_PUSH_EMAIL_AUTH_USER`、`MCP_PUSH_EMAIL_AUTH_PASS`、`MCP_PUSH_EMAIL_TO_ADDRESS`；端口 `MCP_PUSH_EMAIL_PORT` 默认 465，类型 `MCP_PUSH_EMAIL_TYPE` 默认 text |
| `ServerChanTurbo` | `MCP_PUSH_SERVER_CHAN_TURBO_SENDKEY` |
| `ServerChanV3` | `MCP_PUSH_SERVER_CHAN_V3_SENDKEY` |
| `PushPlus` | `MCP_PUSH_PUSH_PLUS_TOKEN` |
| `WxPusher` | `MCP_PUSH_WX_PUSHER_APP_TOKEN`、`MCP_PUSH_WX_PUSHER_UID` |
| `Discord` | `MCP_PUSH_DISCORD_WEBHOOK` |
| `Ntfy` | `MCP_PUSH_NTFY_URL`、`MCP_PUSH_NTFY_TOPIC`、可选 `MCP_PUSH_NTFY_AUTH` |
| `OneBot` | `MCP_PUSH_ONE_BOT_BASE_URL`、可选 `MCP_PUSH_ONE_BOT_ACCESS_TOKEN` |
| `PushDeer` | `MCP_PUSH_PUSH_DEER_PUSH_KEY`、可选 `MCP_PUSH_PUSH_DEER_ENDPOINT` |
| `IGot` | `MCP_PUSH_I_GOT_KEY` |
| `Qmsg` | `MCP_PUSH_QMSG_KEY` |
| `XiZhi` | `MCP_PUSH_XI_ZHI_KEY`（上游已标记该渠道服务停止） |

代理可配置 `MCP_PUSH_HTTP_PROXY`、`MCP_PUSH_HTTPS_PROXY`、`MCP_PUSH_SOCKS_PROXY`；`MCP_PUSH_NO_PROXY=true` 按上游规则禁用代理。浏览器来源默认只允许 Nginx 公开地址，额外来源可用 `MCP_PUSH_ALLOWED_ORIGINS` 配置，多个地址用逗号分隔；普通 MCP 客户端无需发送 Origin。

修改配置后执行 `ct-cntr up mcp-push` 重新创建容器。一个实例为每个渠道保存一套配置；接收者等发送选项由 `options` 指定。容器没有本地消息队列或数据库，配置持久化由 `ct-cntr` 管理。

## MCP 工具

- `list_push_channels`：列出渠道、缺失的配置键和发送选项；可用 `channel` 筛选。不会返回配置值。
- `send_push`：使用 `channel`、`title`、`body` 和可选 `options` 发送消息。返回上游状态与响应，已知渠道错误会标为 `isError`。请求超时不代表未送达，服务不会自动重试。

企业微信示例：

```json
{
  "channel": "WechatRobot",
  "title": "任务完成",
  "body": "备份已完成。",
  "options": { "msgtype": "text" }
}
```

发送选项沿用上游 API；飞书等渠道还需要在 `options` 中指定接收者。邮件选项禁止读取容器文件或从 URL 加载附件。

## 独立 Docker 部署

```bash
docker build -f .github/dockerfiles/mcp-push.Dockerfile -t mcp-push .
docker run -d --name mcp-push -p 8931:8931 \
  -e MCP_PUSH_TOKEN=替换为至少32位的随机Token \
  -e MCP_PUSH_WECHAT_ROBOT_KEY=你的机器人Key \
  mcp-push
```

健康检查为 `/health`；该路径只用于容器健康检查，Nginx 仅代理 `/mcp`。
