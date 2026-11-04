# Guacamole

单人使用的浏览器远程桌面入口，支持 Windows RDP 和 macOS VNC。公网入口由 Nginx HTTPS + Authelia ForwardAuth 保护；通过认证后，Nginx 固定传递 `REMOTE_USER=guacadmin`，Guacamole 使用 PostgreSQL JDBC 保存连接和权限。

## 部署

1. 安装 `nginx`、`authelia` 和 `guacamole`。要求 `NGINX_HTTPS_ENABLE=true`、`NGINX_AUTH_ENABLE=true`；Guacamole 站点强制 HTTPS 和认证。
2. 运行 `ct-cntr add guacamole`、`ct-cntr up guacamole`。要求 PostgreSQL 数据目录为空；首次启动自动初始化官方表结构及管理员，无需手动执行 SQL。已有数据卷不执行自动补齐或迁移。
3. 使用 `https://guacamole.<root-domain>/`（端口取 `NGINX_HTTPS_PORT`）访问。Authelia 验证成功后直接进入 Guacamole，不需要第二套登录密码。
4. 在 Guacamole 管理界面添加 Windows RDP 或 macOS VNC 连接。Windows 使用内网 RDP 端口 3389；Mac 开启屏幕共享及第三方 VNC 访问，使用内网 5900 和独立 VNC 密码。目标 RDP/VNC 不发布公网端口。

可配置字段：`GUACAMOLE_TAG`（默认 1.6.0，guacamole/guacd 同版本）、`GUACAMOLE_DOMAIN`、`GUACAMOLE_DB_PASSWORD`（自动生成并缓存）。PostgreSQL 固定 16-alpine，数据位于应用持久目录 `postgres/`。

## 单用户身份与权限

- 通过 endpoint 的 `auth_headers` 声明 `REMOTE_USER=guacadmin`；Nginx 框架仅在 Authelia 认证成功后注入该固定身份，并覆盖客户端传入的同名请求头。客户端不能通过伪造请求头切换身份。无需自定义 Nginx 模板。
- PostgreSQL 首次初始化通过 Guacamole 官方 `initdb.sh` 生成表结构及管理员，再执行 `scripts/admin.sql` 将官方 `guacadmin/guacadmin` 密码哈希替换为随机值。账号通过 Header Auth 登录，不保留已知默认密码。
- 管理员权限完全由 Guacamole 官方初始化脚本创建；项目只负责消除官方默认密码。数据库只在空数据目录首次启动时初始化，后续重启保留已有连接和权限。
- **所有能够通过该 Authelia 站点认证的用户都会映射到同一个 Guacamole 管理员。** 此配置仅适用于单人使用；不要将该站点授权给其他用户。

## 网络与数据安全

- Guacamole Web、guacd 和 PostgreSQL 均不发布宿主机端口。Guacamole Web 加入现有 `nginx` 网络；guacd 和 PostgreSQL 只加入私有 `guacamole` 网络。
- 共享 `nginx` Docker 网络内的其他容器仍可能直连 Guacamole 并伪造身份头；该网络只能容纳受信任的容器，不可连接不可信工作负载或映射 Guacamole 8080 端口。
- PostgreSQL Dockerfile 构建阶段调用官方 `/opt/guacamole/bin/initdb.sh --postgresql`，仍生成 `guacamole.sql`；复制到初始化目录时命名为 `001-guacamole.sql`，将源文件 `scripts/admin.sql` 复制为 `002-secure-admin.sql`。新数据卷按编号顺序执行，不需要额外启动钩子。
- `scripts/admin.sql` 仅替换新库的 `guacadmin` 默认密码哈希，不负责创建账号、补齐权限或迁移已有数据库。升级 `GUACAMOLE_TAG` 不会自动迁移已有数据库；变更官方初始化 SQL 时须核对默认管理员及 JDBC schema。
- RDP/VNC 目标账户及密码由 Guacamole 保存在 PostgreSQL；不在浏览器中下发明文凭据。数据库持久卷及备份应限制访问；应用或数据库重启可能断开已有桌面会话。

## 验收

1. Compose 渲染无 `ports`；Guacamole 接入 `nginx`、`guacamole` 网络，guacd/数据库仅加入 `guacamole` 网络；仅 PostgreSQL 服务自动注入 `build`。
2. Nginx 原生 `nginx -t` 通过；未通过 Authelia 认证的请求不转发，客户端伪造 `REMOTE_USER` 不能切换 Guacamole 身份。
3. 空数据卷自动创建管理员并替换默认密码；已有数据卷不会重新初始化或自动补齐权限。
4. RDP、VNC、WebSocket 与剪贴板按目标系统实测；DB 重启后保留连接、权限、凭据。
