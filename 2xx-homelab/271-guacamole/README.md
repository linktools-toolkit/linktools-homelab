# Guacamole

浏览器访问 Windows RDP 和 macOS VNC。使用 Nginx HTTPS + Authelia ForwardAuth；Guacamole 的 HTTP Header 扩展读取经过认证的 `REMOTE_USER`，PostgreSQL JDBC 管理连接和权限。此方案不启用 Guacamole 原生 OIDC。

## 部署

1. 安装 `nginx`、`authelia` 和 `guacamole`。要求 `NGINX_HTTPS_ENABLE=true`、`NGINX_AUTH_ENABLE=true`；Guacamole 站点强制 HTTPS 和认证，关闭这两个全局能力时配置校验失败。
2. 运行 `ct-cntr add guacamole`、`ct-cntr up guacamole`。数据库仅初始化官方表结构，**不会预创建任何 Guacamole 管理员账号**。
3. 使用 `https://guacamole.<root-domain>/`（端口取 `NGINX_HTTPS_PORT`）访问。Authelia 验证成功后无需第二套 Guacamole 登录密码；首次登录时 PostgreSQL 自动创建对应的普通账号，默认不拥有管理或桌面连接权限。
4. 需要使用 Web 管理界面配置连接时，先按下方“首次管理员授权”步骤，**显式授权**你指定的 Authelia 用户。Windows 使用内网 RDP 端口 3389；Mac 开启屏幕共享及第三方 VNC 访问，使用内网 5900 和独立 VNC 密码。目标 RDP/VNC 不发布公网端口。

可配置字段：`GUACAMOLE_TAG`（默认 1.6.0，guacamole/guacd 同版本）、`GUACAMOLE_DOMAIN`、`GUACAMOLE_DB_PASSWORD`（自动生成并缓存）。PostgreSQL 固定 16-alpine，数据位于应用持久目录 `postgres/`。


## 首次管理员授权（按需手动执行）

**没有默认管理员账号。** 如果需要在 Guacamole 管理界面添加连接、分配权限，先用准备授权的 Authelia 用户登录 Guacamole 一次，使 `POSTGRESQL_AUTO_CREATE_ACCOUNTS=true` 在数据库创建该普通账号。随后由具有 Docker/数据库管理权限的操作者执行一次显式授权：

1. 在宿主机执行 `docker ps --filter label=com.docker.compose.service=guacamole-postgres`，确认正确项目对应的 PostgreSQL 容器 ID；不要使用其他项目的同名服务。
2. 把以下命令中的 `<postgres-container-id>` 和 `<authelia-username>` 换成实际值。用户名必须与登录后 Guacamole 中的用户名完全一致（区分大小写）。

```sh
docker exec -i <postgres-container-id> psql \
  -U guacamole -d guacamole -v ON_ERROR_STOP=1 \
  -v login='<authelia-username>' <<'SQL'
BEGIN;
INSERT INTO guacamole_system_permission (entity_id, permission)
SELECT e.entity_id, p.permission::guacamole_system_permission_type
FROM guacamole_entity AS e
CROSS JOIN (
    VALUES ('CREATE_CONNECTION'), ('CREATE_CONNECTION_GROUP'),
           ('CREATE_SHARING_PROFILE'), ('CREATE_USER'),
           ('CREATE_USER_GROUP'), ('ADMINISTER')
) AS p(permission)
WHERE e.name = :'login' AND e.type = 'USER'
ON CONFLICT DO NOTHING;
INSERT INTO guacamole_user_permission (entity_id, affected_user_id, permission)
SELECT e.entity_id, u.user_id, p.permission::guacamole_object_permission_type
FROM guacamole_entity AS e
JOIN guacamole_user AS u ON u.entity_id = e.entity_id
CROSS JOIN (VALUES ('READ'), ('UPDATE'), ('ADMINISTER')) AS p(permission)
WHERE e.name = :'login' AND e.type = 'USER'
ON CONFLICT DO NOTHING;
COMMIT;
SELECT permission FROM guacamole_system_permission AS p
JOIN guacamole_entity AS e ON e.entity_id = p.entity_id
WHERE e.name = :'login' AND e.type = 'USER'
ORDER BY permission;
SQL
```

检查命令末尾返回了 `ADMINISTER` 等权限；如果没有，先确认该用户已通过 Authelia 登录并自动创建。此后该用户重新登录 Guacamole 即可使用管理界面。此操作不会自动授予其他用户管理权限；需要另行指定其他管理员时重复显式授权。

## 身份与安全边界

- Nginx 对全部 Guacamole 请求（包括 WebSocket）执行 Authelia `auth_request`；从验证成功的 `Remote-User` 构造身份变量，并通过 `proxy_set_header REMOTE_USER` **覆盖客户端同名请求头**。身份缺失不授予远程桌面连接权限；Authelia 拒绝的请求不会转发。
- Guacamole Web、guacd 和 PostgreSQL 均不发布宿主机端口。Guacamole 必须加入现有 `nginx` 桥接网络，因此**同一 Docker 网络的其他容器可以直连其 HTTP 服务并伪造头**：该网络必须仅包含可信容器，不可连接不可信工作负载或映射 Guacamole 8080 端口。公网请求只经过 Nginx。
- PostgreSQL 首次启动仅加载 Apache Guacamole 1.6.0 官方 **`001-create-schema.sql` 表结构**，不运行上游创建 `guacadmin/guacadmin` 的 `002-create-admin-user.sql`，也不创建自定义默认管理员。管理员权限只能在首次登录后通过明确的数据库授权操作授予指定账号。
- `POSTGRESQL_AUTO_CREATE_ACCOUNTS` 允许经 Header Auth 登录的新用户在数据库中自动创建账号，但只获得自身 READ 权限；桌面连接与管理权限须管理员显式授予。RDP/VNC 目标账户及密码由 Guacamole 保存在 PostgreSQL，不在浏览器中下发明文凭据。
- Nginx/Authelia 是唯一的**公网**认证入口，不提供 Guacamole 独立外网登录入口。Authelia 不可用时不能从 Nginx 入口登录。PostgreSQL 不可用时 Web 服务不能正常提供连接数据；guacd 不可用时桌面连接失败。

## 数据库生命周期

`001-create-schema.sql` 原样来自 [Apache Guacamole 1.6.0 JDBC PostgreSQL schema](https://github.com/apache/guacamole-client/blob/1.6.0/extensions/guacamole-auth-jdbc/modules/guacamole-auth-jdbc-postgresql/schema/001-create-schema.sql)（Apache-2.0）。不执行任何账户或管理员创建 SQL。PostgreSQL initdb 脚本只会在**空数据库目录首次启动**时执行，重启不会重设权限或数据。升级 Guacamole TAG 前须依据官方说明完成 JDBC schema 迁移。对数据库持久卷及备份采取访问限制；应用或数据库重启可能断开已有桌面会话。

## 验收

1. 检查 Compose 渲染无 `ports`；Guacamole 接入 `nginx`、`guacamole` 网络，guacd/数据库仅加入 `guacamole` 网络。
2. Nginx 原生 `nginx -t` 通过；所有请求均经过 Authelia 认证，用户伪造 `REMOTE_USER` 不能冒用其他账号。
3. 首次部署没有任何预置 Guacamole 管理员；Authelia 首次登录仅创建普通 JDBC 账号；管理员显式授权后才可管理连接，其他账号仅可访问显式授权的连接。
4. RDP、VNC、WebSocket 与剪贴板按目标系统实测；DB 重启后保留连接、权限、凭据；无默认 Guacamole 密码账号。
