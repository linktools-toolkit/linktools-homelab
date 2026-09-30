# Playwright MCP + noVNC

一个容器内运行 Chromium、Playwright MCP、Xvfb、Openbox、x11vnc 和 noVNC。
Chromium 随容器启动，无需先调用 MCP；网页操作和 MCP 通过 CDP 使用同一个浏览器。

## 部署

```bash
ct-cntr up mcp-playwright
```

服务名和镜像名已由 `playwright-mcp` 改为 `mcp-playwright`，配置键统一使用 `MCP_PLAYWRIGHT_*`。
已有部署迁移时，先停止旧服务，再将旧服务的 `APP_PATH/home` 迁移到新服务的 `APP_PATH/home`，保留文件属主，以保留浏览器登录数据。
将原有域名、Token 和端口配置以新键名设置到新服务后再启动（例如 `PLAYWRIGHT_MCP_TOKEN` 改为 `MCP_PLAYWRIGHT_TOKEN`）；旧配置键不再读取。若未指定域名，默认域名会随服务名改变。

从服务列表打开 **Playwright Browser**，或访问配置的 `MCP_PLAYWRIGHT_DOMAIN`：

```text
https://<MCP_PLAYWRIGHT_DOMAIN>/vnc.html?autoconnect=true&resize=scale
```

noVNC 页面及 WebSocket 沿用 nginx / Authelia 登录保护。根路径也可打开 noVNC，点击 Connect 后即可操作浏览器。

## MCP 连接

Nginx 将同一域名的 `/mcp` 转发到 MCP 服务，无需开放宿主机端口。
MCP 使用独立的 Bearer Token，不跳转到 Authelia 登录页。Token 首次自动生成并缓存，运行以下命令可打印完整的 MCP 客户端 JSON 配置（包含 URL 和 Bearer Token）：

```bash
ct-cntr exec mcp-playwright show
```

将输出复制到 MCP 客户端配置：

```json
{
  "mcpServers": {
    "playwright": {
      "url": "https://<MCP_PLAYWRIGHT_DOMAIN>/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_PLAYWRIGHT_TOKEN>"
      }
    }
  }
}
```

缺少或携带错误 Token 时返回 HTTP 401。Nginx 支持 MCP 流式响应及会话头；noVNC 的认证不受此 Token 影响。
Token 可通过 `ct-cntr config set MCP_PLAYWRIGHT_TOKEN=<新Token>` 修改，要求 32–128 位字母、数字、下划线或连字符；修改后执行 `ct-cntr up mcp-playwright` 更新 Nginx 配置。

同一 `nginx` Docker 网络内仍可直连 `http://mcp-playwright:8931/mcp`。需要从宿主机或局域网直连时，开启相应端口后重新部署：

```bash
ct-cntr config set MCP_PLAYWRIGHT_PORT=8931 MCP_PLAYWRIGHT_NOVNC_PORT=6080
ct-cntr up mcp-playwright
```

- MCP：`http://<服务器IP>:8931/mcp`
- 浏览器：`http://<服务器IP>:6080/vnc.html?autoconnect=true&resize=scale`

直连端口默认关闭；Docker 内网及宿主机端口直连均绕过 Nginx 的 Bearer Token / Authelia 认证，仅供可信网络使用。原始 VNC（5900）和 CDP（9222）仅监听容器回环地址，不发布到宿主机。

## 配置与数据

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| `MCP_PLAYWRIGHT_TAG` | `latest` | GHCR 镜像标签，可指定 npm 版本，例如 `0.0.83` |
| `MCP_PLAYWRIGHT_DOMAIN` | 框架分配 | noVNC 和 MCP 共用域名 |
| `MCP_PLAYWRIGHT_TOKEN` | 自动生成并缓存 | Nginx `/mcp` 入口的 Bearer Token |
| `MCP_PLAYWRIGHT_PORT` | `0` | MCP 宿主机端口，0 为关闭 |
| `MCP_PLAYWRIGHT_NOVNC_PORT` | `0` | noVNC 宿主机端口，0 为关闭 |
| `MCP_PLAYWRIGHT_SCREEN_WIDTH` | `1440` | 桌面宽度 |
| `MCP_PLAYWRIGHT_SCREEN_HEIGHT` | `900` | 桌面高度 |

`APP_PATH/home` 持久化到 `/workspace`，其中 `profile/` 保存浏览器登录态，`output/` 保存 MCP 输出。
不要让多个容器同时使用同一个 profile。所有 MCP 客户端和 noVNC 用户共享页面、Cookie 和登录态；同时操作会互相影响。
关闭整个浏览器窗口会触发容器重启，再次打开 noVNC 即可连接。

镜像由 `master` 分支的 `.github/workflows/build-mcp-playwright.yml` 构建并发布到 `ghcr.io/linktools-toolkit/mcp-playwright`，部署时直接拉取，无需本地构建。
Workflow 支持每天检查 npm 更新、手动指定版本和强制重建；镜像相关文件推送到 `master` 时也会触发。发布前检查浏览器启动、noVNC WebSocket 和 MCP 共享浏览器。镜像安装指定 MCP 版本对应的 Chromium，避免版本不匹配。
容器使用项目配置的普通用户运行；Chromium 在容器内以 `--no-sandbox` 启动。
使用 `--test-type` 自动化测试模式隐藏启动参数警告栏；此设置不会启用 Chromium 沙箱。

上游文档：[Playwright MCP](https://github.com/microsoft/playwright-mcp)、[noVNC](https://github.com/novnc/noVNC)。

镜像构建参数为 `MCP_PLAYWRIGHT_VERSION`；桌面分辨率环境变量为 `MCP_PLAYWRIGHT_SCREEN_WIDTH` 和 `MCP_PLAYWRIGHT_SCREEN_HEIGHT`。Playwright 自身要求的 `PLAYWRIGHT_BROWSERS_PATH` 保持上游名称。
