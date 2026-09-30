# Push MCP

基于 [push-all-in-one](https://github.com/CaoMeiYouRen/push-all-in-one) 的推送 MCP 服务。提供 Streamable HTTP `/mcp`，支持多个客户端并发调用，通过 Nginx 暴露。服务端和直连端口均校验 Bearer Token。

## 部署与配置

镜像由 `.github/workflows/build-mcp-push.yml` 构建并发布到 `ghcr.io/linktools-toolkit/mcp-push`。首次部署前需先发布镜像。Workflow 支持手动指定上游 npm 版本、强制重建、每日检查更新，以及镜像源文件推送到 `master` 时重建；发布前用本机模拟渠道检查 MCP，不发送真实通知。

机器人凭据可以放在 MCP 客户端的 HTTP headers 中，服务端每次调用时直接读取，不需要把这些值保存到容器配置。`show` 支持按渠道生成示例；例如打印飞书配置：

```bash
ct-cntr up mcp-push
ct-cntr exec mcp-push show Feishu
```

命令会打印包含 URL、Bearer Token 和飞书 header 占位值的 JSON。将两个占位值替换为飞书应用的 App ID 和 App Secret 后，复制到 MCP 客户端：

```json
{
  "mcpServers": {
    "push": {
      "url": "https://<MCP_PUSH_DOMAIN>/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_PUSH_TOKEN>",
        "X-CHANNEL": "Feishu",
        "X-FEISHU-APP-ID": "<FEISHU_APP_ID>",
        "X-FEISHU-APP-SECRET": "<FEISHU_APP_SECRET>"
      }
    }
  }
}
```

`MCP_PUSH_DOMAIN` 默认由框架分配。`MCP_PUSH_TOKEN` 首次自动生成并缓存，也可自行设置至少 32 位、不含空白的字符串。`MCP_PUSH_TAG` 默认为 `latest`，可指定上游版本标签（例如 `4.5.4`）。`MCP_PUSH_PORT` 默认为 `0`；设为非零后可通过 `http://<主机IP>:<端口>/mcp` 访问，同样需要 Token。容器网络内地址为 `http://mcp-push:8931/mcp`。

## 渠道参数

在 MCP 客户端的 HTTP headers 中用 `X-CHANNEL` 固定该客户端使用的渠道，例如 `Feishu`。服务端根据渠道读取对应配置头，例如 `X-FEISHU-APP-ID` 和 `X-FEISHU-APP-SECRET`；字段名由上游配置名转换而来（下划线改为连字符，并加 `X-` 前缀）。缺失配置会在 `send_push` 的错误结果中列出需要的 header 名称。渠道配置只从请求头读取，不保存到容器，也不会作为 MCP 工具参数暴露给模型。MCP 客户端必须在每次 HTTP 请求中附带这些 headers。不带渠道参数执行 `ct-cntr exec mcp-push show` 会打印通用配置；MCP 服务仍支持下表中的所有上游渠道，`show <渠道>` 的配置示例仅保留上游 README 标注为推荐的 `ServerChanV3`、`CustomEmail`、`Dingtalk`、`WechatApp`、`Feishu`、`Discord`、`Telegram` 和 `Ntfy`。

| MCP 渠道名 | 常用 header |
| --- | --- |
| `WechatRobot` | `X-WECHAT-ROBOT-KEY` |
| `WechatApp` | `X-WECHAT-APP-CORPID`、`X-WECHAT-APP-SECRET`、`X-WECHAT-APP-AGENTID` |
| `Dingtalk` | `X-DINGTALK-ACCESS-TOKEN`、可选 `X-DINGTALK-SECRET` |
| `Feishu` | `X-FEISHU-APP-ID`、`X-FEISHU-APP-SECRET` |
| `Telegram` | `X-TELEGRAM-BOT-TOKEN`、`X-TELEGRAM-CHAT-ID` |
| `CustomEmail` | `X-EMAIL-HOST`、`X-EMAIL-AUTH-USER`、`X-EMAIL-AUTH-PASS`、`X-EMAIL-TO-ADDRESS`；端口 `X-EMAIL-PORT` 默认 465，类型 `X-EMAIL-TYPE` 默认 text |
| `ServerChanTurbo` | `X-SERVER-CHAN-TURBO-SENDKEY` |
| `ServerChanV3` | `X-SERVER-CHAN-V3-SENDKEY` |
| `PushPlus` | `X-PUSH-PLUS-TOKEN` |
| `WxPusher` | `X-WX-PUSHER-APP-TOKEN`、`X-WX-PUSHER-UID` |
| `Discord` | `X-DISCORD-WEBHOOK` |
| `Ntfy` | `X-NTFY-URL`、`X-NTFY-TOPIC`、可选 `X-NTFY-AUTH` |
| `OneBot` | `X-ONE-BOT-BASE-URL`、可选 `X-ONE-BOT-ACCESS-TOKEN` |
| `PushDeer` | `X-PUSH-DEER-PUSH-KEY`、可选 `X-PUSH-DEER-ENDPOINT` |
| `IGot` | `X-I-GOT-KEY` |
| `Qmsg` | `X-QMSG-KEY` |
| `XiZhi` | `X-XI-ZHI-KEY`（上游已标记该渠道服务停止） |

发送参数也可以固定在请求头中，头名称为 `X-<参数名>`，参数名中的下划线和驼峰边界转换为连字符并大写。例如飞书接收者可以写成 `X-RECEIVE-ID`。`X-CHANNEL` 保留用于选择推送渠道；若要通过 header 固定 PushPlus 的 `channel` 参数，使用 `X-ARG-CHANNEL`。服务端在 `tools/list` 时会隐藏已通过请求头提供的参数，并在调用时从请求头读取；因此 MCP 客户端需要在列出工具和调用工具时都发送相同的 headers。ASCII 字符串直接传值；含中文等非 ASCII 字符时，对 UTF-8 值进行百分号编码。数字传数字文本，布尔值传 `true` 或 `false`，数组和对象传 JSON（含非 ASCII 字符时对整个 JSON 编码），枚举值必须匹配上游允许值。

可为同一 URL 配置多个 MCP server 条目，每个条目使用不同的 `X-CHANNEL` 和对应凭据，从而让同一客户端连接多个渠道。代理可配置 `MCP_PUSH_HTTP_PROXY`、`MCP_PUSH_HTTPS_PROXY`、`MCP_PUSH_SOCKS_PROXY`；`MCP_PUSH_NO_PROXY=true` 按上游规则禁用代理。浏览器来源默认允许 Nginx 公开地址，也可通过 `ct-cntr config set 'MCP_PUSH_ALLOWED_ORIGINS=https://extra.example.com,https://localhost:3000'` 追加来源，多个地址用逗号分隔；普通 MCP 客户端无需发送 Origin。

header 中的字段按请求生效，不同 MCP 客户端可以使用各自的机器人凭据。`MCP_PUSH_TOKEN` 是 MCP 服务自身的访问令牌，与机器人凭据分开。

## MCP 工具

- `send_push`：渠道从 `X-CHANNEL` 读取。服务端根据该请求头动态生成渠道专属的工具参数，直接列出字段名、类型、描述、枚举值和必填项，并拒绝未声明的字段。调用 `tools/list` 时也必须携带该请求头。未设置渠道或缺少渠道配置时会返回对应提示。返回上游状态与响应，已知渠道错误会标为 `isError`。请求超时不代表未送达，服务不会自动重试。

企业微信示例：

```json
{
  "title": "任务完成",
  "body": "备份已完成。",
  "msgtype": "text"
}
```

飞书的工具参数会明确列出 `receive_id_type` 的可选值、必填的 `receive_id` 和 `msg_type`；文本消息可以省略 `content`，服务会用 `title` 和 `body` 生成内容：

```json
{
  "title": "任务完成",
  "body": "备份已完成。",
  "receive_id_type": "chat_id",
  "receive_id": "oc_xxx",
  "msg_type": "text"
}
```

如果接收者固定在 MCP 客户端配置中，可以加上这些 headers：

```json
{
  "X-CHANNEL": "Feishu",
  "X-FEISHU-APP-ID": "<FEISHU_APP_ID>",
  "X-FEISHU-APP-SECRET": "<FEISHU_APP_SECRET>",
  "X-RECEIVE-ID-TYPE": "chat_id",
  "X-RECEIVE-ID": "oc_xxx",
  "X-MSG-TYPE": "text"
}
```

这时 `tools/list` 返回的 `send_push` 参数中不会出现 `receive_id_type`、`receive_id` 和 `msg_type`，调用时也无需再传它们。

渠道专属参数沿用上游 API。邮件选项禁止读取容器文件或从 URL 加载附件。

## 独立 Docker 部署

```bash
docker build -f .github/docker/mcp-push/Dockerfile -t mcp-push .
docker run -d --name mcp-push -p 8931:8931 \
  -e MCP_PUSH_TOKEN=替换为至少32位的随机Token \
  mcp-push
```

健康检查为 `/health`；该路径只用于容器健康检查，Nginx 仅代理 `/mcp`。
