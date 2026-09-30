# Multica Server

## 渠道加密密钥

`configs` 为飞书、Slack、钉钉、企业微信和 Telegram 提供默认加密密钥，由 Compose 显式注入：
`MULTICA_LARK_SECRET_KEY`、`MULTICA_SLACK_SECRET_KEY`、`MULTICA_DINGTALK_SECRET_KEY`、`MULTICA_WECOM_SECRET_KEY`、`MULTICA_TELEGRAM_SECRET_KEY`。
首次使用时各自生成独立的 32 字节随机值并进行 Base64 编码，缓存到配置中，后续部署复用；已有配置优先，不会被覆盖。显式配置空字符串可禁用对应渠道集成。

执行 `ct-cntr up multica-server` 后注入后端。仍需在界面填写各平台的应用或机器人凭据并完成连接。已保存渠道凭据后请保留这些加密密钥，删除或更换会导致原凭据无法解密。

## 动态环境变量

GitHub App 使用 `configs` 中的 `MULTICA_GITHUB_APP_SLUG`、`MULTICA_GITHUB_WEBHOOK_SECRET`、`MULTICA_GITHUB_APP_ID` 和 `MULTICA_GITHUB_APP_PRIVATE_KEY`，Compose 将它们映射为后端要求的 `GITHUB_*`。Webhook secret 默认随机生成并缓存，也可设置为创建 App 时填写的同一密钥。私钥填写完整 PEM（保留换行和 BEGIN/END 行）。

在 GitHub Developer settings → GitHub Apps 创建 App：Homepage URL 填 Multica 公开地址，Callback URL 留空，Setup URL 填 `<公开地址>/api/github/setup` 并启用 Redirect on update，Webhook URL 填 `<公开地址>/api/webhooks/github`。授予 Metadata、Pull requests、Checks、Commit statuses 只读权限，订阅 Pull request、Check suite、Check run、Status 事件。配置并重新部署后，在 Multica 的 GitHub 设置中连接并授权仓库。详见[上游说明](https://github.com/multica-ai/multica/blob/main/apps/docs/content/docs/github-integration.mdx)。

直接通过配置设置 `MULTICA_` 开头的变量，部署时自动注入后端：

```bash
ct-cntr config set multica-server MULTICA_WECOM_KEY=your-key
ct-cntr up multica-server
```

后端收到的变量名仍为 `MULTICA_WECOM_KEY`，不会自动去掉前缀。变量名需与实际程序读取的名称一致；注入变量本身不会增加企业微信集成功能。

可以逐项增加、修改或删除配置，无需维护 JSON 字典：

```bash
ct-cntr config unset MULTICA_WECOM_KEY
ct-cntr up multica-server
```

修改后重新部署生效，不是运行时热加载。变量仅注入 `multica-backend`，不会传给前端、数据库或独立 Agent/daemon。

`container.py` 使用与 Nginx 相同的 `@cached_property extend_configs` 扩展入口：发现配置源中已有的 `MULTICA_*` 键，为其创建带缓存交互提示的 `ConfigField`。已有配置值直接使用，不会再次询问；允许空字符串。扩展项也会出现在 `ct-cntr config list multica-server` 中。扩展项排除 `multica-server` 自身的 `configs`；仅当 `multica` 存在且已启用时，也排除它的 `configs`。不再按全局 schema 排除其他声明。

## 注入规则

`compose.yml` 仅遍历 `container.extend_configs`，所有扩展项按原名注入。变量渲染和转义直接写在 Compose 中，原有环境变量声明保持不变。

`multica-server.configs` 中的配置不会动态注入；`multica` 启用时，其 `configs` 中的配置也不会动态注入。若 `multica` 未启用，配置源中遗留的同名前缀配置也会被当作扩展项，删除不需要透传的旧配置即可。

扩展项位于环境变量列表末尾；同名扩展项覆盖原有值，例如 `MULTICA_PUBLIC_URL` 可以覆盖域名生成的公开 URL。
建议使用字符串配置值；布尔值转换为 `true` / `false`，数字转换为字符串，支持空字符串。Compose 渲染会转义 `$`、引号和换行。

自定义敏感扩展项可在 `extend_configs` 创建对应 `ConfigField` 时标记 `secret=True`。
