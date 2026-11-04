# Guacamole

单人使用的浏览器远程桌面入口，支持 Windows RDP 和 macOS VNC。公网入口由 Nginx HTTPS + Authelia ForwardAuth 保护；通过认证后，Nginx 固定传递 `REMOTE_USER=guacadmin`，Guacamole 使用 PostgreSQL JDBC 保存连接和权限。

## 部署

1. 安装 `nginx`、`authelia` 和 `guacamole`。要求 `NGINX_HTTPS_ENABLE=true`、`NGINX_AUTH_ENABLE=true`；Guacamole 站点强制 HTTPS 和认证。
2. 运行 `ct-cntr add guacamole`、`ct-cntr up guacamole`。首次部署会初始化数据库表和固定管理员；已有数据库也会在启动后自动补齐管理员权限，不需要手动执行 SQL。
3. 使用 `https://guacamole.<root-domain>/`（端口取 `NGINX_HTTPS_PORT`）访问。Authelia 验证成功后直接进入 Guacamole，不需要第二套登录密码。
4. 在 Guacamole 管理界面添加 Windows RDP 或 macOS VNC 连接。Windows 使用内网 RDP 端口 3389；Mac 开启屏幕共享及第三方 VNC 访问，使用内网 5900 和独立 VNC 密码。目标 RDP/VNC 不发布公网端口。

可配置字段：`GUACAMOLE_TAG`（默认 1.6.0，guacamole/guacd 同版本）、`GUACAMOLE_DOMAIN`、`GUACAMOLE_DB_PASSWORD`（自动生成并缓存）。PostgreSQL 固定 16-alpine，数据位于应用持久目录 `postgres/`。

## 单用户身份与权限

- 通过 endpoint 的 `auth_headers` 声明 `REMOTE_USER=guacadmin`；Nginx 框架仅在 Authelia 认证成功后注入该固定身份，并覆盖客户端传入的同名请求头。客户端不能通过伪造请求头切换身份。无需自定义 Nginx 模板。
- PostgreSQL 首次初始化通过 Guacamole 官方 `initdb.sh` 生成表结构及默认管理员，再执行 `scripts/admin.sql` 将官方 `guacadmin/guacadmin` 密码替换为随机哈希。账号通过 Header Auth 登录，最终不保留已知默认密码。
- `on_started` 每次部署后幂等执行同一初始化 SQL，因此已经存在的 PostgreSQL 数据卷也会自动补齐管理员，不会删除既有用户、连接、权限或凭据。
- **所有能够通过该 Authelia 站点认证的用户都会映射到同一个 Guacamole 管理员。** 此配置仅适用于单人使用；不要将该站点授权给其他用户。

## 网络与数据安全

- Guacamole Web、guacd 和 PostgreSQL 均不发布宿主机端口。Guacamole Web 加入现有 `nginx` 网络；guacd 和 PostgreSQL 只加入私有 `guacamole` 网络。
- 共享 `nginx` Docker 网络内的其他容器仍可能直连 Guacamole 并伪造身份头；该网络只能容纳受信任的容器，不可连接不可信工作负载或映射 Guacamole 8080 端口。
- PostgreSQL Dockerfile 构建阶段调用官方 `/opt/guacamole/bin/initdb.sh --postgresql`，将完整输出保存为 `guacamole.sql`；镜像初始化先执行该文件，再执行 `secure-admin.sql`（源文件 `scripts/admin.sql`）。已有数据卷由 `on_started` 通过 `docker exec -i ... psql` 的标准输入执行同一份 `scripts/admin.sql`，无需重建或清空数据库。
- 管理员脚本对缺失的账号与权限幂等补齐；仅当 `guacadmin` 的密码哈希和盐与 Guacamole 1.6.0 官方已知默认值一致时，才替换为随机值，不覆盖其他已有密码或连接。升级 `GUACAMOLE_TAG` 不会自动迁移已有数据库；变更官方初始化 SQL 时须重新核对默认凭据及 JDBC schema 迁移要求。
- RDP/VNC 目标账户及密码由 Guacamole 保存在 PostgreSQL；不在浏览器中下发明文凭据。数据库持久卷及备份应限制访问；应用或数据库重启可能断开已有桌面会话。

## 验收

1. Compose 渲染无 `ports`；Guacamole 接入 `nginx`、`guacamole` 网络，guacd/数据库仅加入 `guacamole` 网络；仅 PostgreSQL 服务自动注入 `build`。
2. Nginx 原生 `nginx -t` 通过；未通过 Authelia 认证的请求不转发，客户端伪造 `REMOTE_USER` 不能切换 Guacamole 身份。
3. 新数据卷自动创建管理员；已有数据卷执行 `ct-cntr up guacamole` 后自动补齐管理员权限，无需手动 SQL。
4. RDP、VNC、WebSocket 与剪贴板按目标系统实测；DB 重启后保留连接、权限、凭据。
