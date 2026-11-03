# Guacamole

浏览器访问 Windows RDP 和 macOS VNC。使用 Nginx HTTPS + Authelia ForwardAuth；Guacamole 的 HTTP Header 扩展读取经过认证的 `REMOTE_USER`，PostgreSQL JDBC 管理连接和权限。此方案不启用 Guacamole 原生 OIDC。

## 部署

1. 安装 `nginx`、`authelia` 和 `guacamole`。要求 `NGINX_HTTPS_ENABLE=true`、`NGINX_AUTH_ENABLE=true`；Guacamole 站点强制 HTTPS 和认证，关闭这两个全局能力时配置校验失败。
2. 首次部署前设置 `GUACAMOLE_ADMIN_USERNAME`，使其与 Authelia 提供的用户名完全一致（默认 `admin`）。运行 `ct-cntr add guacamole`、`ct-cntr up guacamole`。
3. 使用 `https://guacamole.<root-domain>/`（端口取 `NGINX_HTTPS_PORT`）访问。Authelia 验证成功后无需第二套 Guacamole 登录密码。管理员在 Guacamole Web 管理界面配置连接和用户授权。
4. Windows 使用内网 RDP 端口 3389；Mac 开启屏幕共享及第三方 VNC 访问，使用内网 5900 和独立 VNC 密码。目标 RDP/VNC 不发布公网端口。

可配置字段：`GUACAMOLE_TAG`（默认 1.6.0，guacamole/guacd 同版本）、`GUACAMOLE_DOMAIN`、`GUACAMOLE_ADMIN_USERNAME`（默认 `admin`）、`GUACAMOLE_DB_PASSWORD`（自动生成并缓存）。PostgreSQL 固定 16-alpine，数据位于应用持久目录 `postgres/`。

## 身份与安全边界

- Nginx 对全部 Guacamole 请求（包括 WebSocket）执行 Authelia `auth_request`；从验证成功的 `Remote-User` 构造身份变量，并通过 `proxy_set_header REMOTE_USER` **覆盖客户端同名请求头**。身份缺失不授予远程桌面连接权限；Authelia 拒绝的请求不会转发。
- Guacamole Web、guacd 和 PostgreSQL 均不发布宿主机端口。Guacamole 必须加入现有 `nginx` 桥接网络，因此**同一 Docker 网络的其他容器可以直连其 HTTP 服务并伪造头**：该网络必须仅包含可信容器，不可连接不可信工作负载或映射 Guacamole 8080 端口。公网请求只经过 Nginx。
- PostgreSQL 首次启动加载 Apache 1.6.0 官方 schema，创建与 `GUACAMOLE_ADMIN_USERNAME` 同名的管理员，使用随机不可知的 JDBC 密码散列。**不会创建默认 guacadmin/guacadmin 账号。** 修改管理用户名需显式调整数据库，不能只改运行配置。
- `POSTGRESQL_AUTO_CREATE_ACCOUNTS` 允许经 Header Auth 登录的新用户在数据库中自动创建账号，但只获得自身 READ 权限；桌面连接与管理权限须管理员显式授予。RDP/VNC 目标账户及密码由 Guacamole 保存在 PostgreSQL，不在浏览器中下发明文凭据。
- Nginx/Authelia 是唯一的**公网**认证入口，不提供 Guacamole 独立外网登录入口。Authelia 不可用时不能从 Nginx 入口登录。PostgreSQL 不可用时 Web 服务不能正常提供连接数据；guacd 不可用时桌面连接失败。

## 数据库生命周期

`001-create-schema.sql` 原样来自 [Apache Guacamole 1.6.0 JDBC PostgreSQL schema](https://github.com/apache/guacamole-client/blob/1.6.0/extensions/guacamole-auth-jdbc/modules/guacamole-auth-jdbc-postgresql/schema/001-create-schema.sql)（Apache-2.0）。`002-bootstrap-admin.sh` 创建映射到 Authelia 的管理用户。PostgreSQL initdb 脚本只会在**空数据库目录首次启动**时执行，重启不会重设管理员或数据。升级 Guacamole TAG 前须依据官方说明完成 JDBC schema 迁移。对数据库持久卷及备份采取访问限制；应用或数据库重启可能断开已有桌面会话。

## 验收

1. 检查 Compose 渲染无 `ports`；Guacamole 接入 `nginx`、`guacamole` 网络，guacd/数据库仅加入 `guacamole` 网络。
2. Nginx 原生 `nginx -t` 通过；所有请求均经过 Authelia 认证，用户伪造 `REMOTE_USER` 不能冒用其他账号。
3. 指定的 Authelia 管理用户无第二次登录即可管理连接；普通用户仅可访问显式授权的连接。
4. RDP、VNC、WebSocket 与剪贴板按目标系统实测；DB 重启后保留连接、权限、凭据；无默认 Guacamole 密码账号。
