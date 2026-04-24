# 在飞牛 OS 上搭一套更省心的 Homelab：用 linktools-cntr 管理反代、证书、SSO、WAF 和导航页

很多人装飞牛 OS 之后，很快就会遇到同一个问题：

NAS 本身很好用，但服务一多，维护就开始变复杂。  
比如我自己常见的需求是：

- 飞牛管理后台要能通过域名访问
- Docker 应用希望统一挂到不同子域名
- HTTPS 证书最好能自动申请和续期
- 管理类服务不想裸奔在公网
- 不想记住十几个系统各自的账号密码
- 容器配置希望可复用、可升级、可迁移
- 重装或换机器时，不想重新点一遍界面、抄一堆 compose

所以我整理了一套基于 `linktools-cntr` 的飞牛 Homelab 实践方案。它不是单个容器的安装教程，而是把「反向代理、自动证书、SSO、WAF、导航页、容器生命周期管理」放到一套可维护的流程里。

项目地址：

- linktools-cntr：<https://github.com/linktools-toolkit/linktools/tree/master/linktools-cntr>
- 飞牛 Homelab 示例仓库：<https://github.com/linktools-toolkit/linktools-homelab>

## 这套方案解决什么问题

传统 Docker 部署常见的问题是：每个应用都有自己的 compose、端口、目录、反代配置和证书配置。刚开始还好，服务多了以后，维护成本会明显上升。

`linktools-cntr` 的思路是：用一个命令行工具统一管理容器仓库、部署列表、配置变量和容器生命周期。

简单理解就是：

- `ct-cntr add`：添加要部署的服务
- `ct-cntr config set`：统一设置域名、端口、数据目录、证书参数
- `ct-cntr up`：生成配置并启动容器
- `ct-cntr repo update`：更新容器仓库
- `ct-cntr restart/down`：统一重启或停止服务

这样后续新增服务、迁移机器、升级配置都会清晰很多。

## 推荐架构

我目前推荐的飞牛公网访问架构是：

```text
公网请求
  |
  v
nginx（TLS 反向代理，ACME 自动证书）
  |
  +--> safeline（雷池 WAF，过滤恶意流量）
  |
  +--> authelia（SSO 单点登录 + 二步验证）
        |
        +--> lldap（轻量 LDAP 用户目录）
  |
  +--> fnOS / Portainer / 其他 Docker 应用
```

这里面几个核心组件的分工很明确：

| 组件 | 作用 |
|------|------|
| nginx | 统一入口、反向代理、HTTPS |
| ACME | 自动申请和续期证书 |
| Safeline | WAF 防护，减少公网暴露风险 |
| Authelia | 单点登录、二步验证 |
| LLDAP | 用户目录 |
| Flare | Homelab 导航页 |
| Portainer | 可视化管理 Docker 容器 |

飞牛本身负责存储、Docker 运行环境和 NAS 管理；`linktools-cntr` 负责把这些服务组织起来。

## 准备条件

建议准备：

1. 一台安装好飞牛 OS 的 NAS
2. 已启用 Docker 服务
3. 一个域名
4. 公网 IP 或可用的内网穿透/转发方案
5. 域名支持泛解析，例如 `*.example.com`

如果是公网 IP 方案，可以在主路由上把外部访问端口映射到飞牛。例如：

- HTTP 入口：`3000`
- HTTPS 入口：`3002`
- WAF 内部入口：`8000`

端口可以按自己的环境调整，不必照抄。

## 安装 linktools-cntr

SSH 登录飞牛后，先准备基础环境：

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip git docker-compose-plugin
```

安装 `linktools-cntr`：

```bash
python3 -m pip install -U linktools linktools-cntr
```

安装完成后，可以先看一下帮助：

```bash
ct-cntr
```

## 添加飞牛 Homelab 容器仓库

添加示例仓库：

```bash
ct-cntr repo add https://github.com/linktools-toolkit/linktools-homelab
```

后续更新仓库可以使用：

```bash
ct-cntr repo update
```

## 添加推荐服务

基础推荐组合：

```bash
ct-cntr add fnos authelia safeline portainer
```

这里的 `fnos` 会带上基础 Homelab 入口和 Flare 导航页。  
`authelia` 用于 SSO 和二步验证，`safeline` 用于 WAF，`portainer` 用于容器可视化管理。

如果还想继续扩展，也可以按需添加其他服务，例如：

```bash
ct-cntr add vscode gitlab home-assistant
```

## 设置数据目录

建议把容器数据放到飞牛的数据盘里，例如：

```bash
ct-cntr config set \
  DOCKER_APP_PATH=/vol1/1000/Apps
```

飞牛重启后，为了让容器自动恢复，建议设置重启策略：

```bash
ct-cntr config set \
  SERVICE_RESTART_POLICY=always
```

## 设置域名和端口

下面以 `example.com` 为例，请换成自己的域名：

```bash
ct-cntr config set \
  NGINX_ROOT_DOMAIN=example.com \
  NGINX_WILDCARD_DOMAIN=true \
  NGINX_HTTPS_ENABLE=true \
  NGINX_HTTP_PORT=3000 \
  NGINX_HTTPS_PORT=3002 \
  NGINX_WAF_PORT=8000
```

配置后，常见入口会类似这样：

| 服务 | 示例地址 |
|------|----------|
| 导航页 | `https://example.com:3000` |
| 飞牛后台 | `https://fn.example.com:3000` |
| SSO | `https://sso.example.com:3000` |
| 雷池 WAF | `https://safeline.example.com:3000` |
| Portainer | `https://portainer.example.com:3000` |

如果你不想带端口访问，也可以在路由器或前置网关上把标准 80/443 转发到对应入口。

## 配置自动证书

`linktools-cntr` 使用 ACME DNS API 方式申请证书。  
比如阿里云 DNS 可以这样配置：

```bash
ct-cntr config set \
  ACME_DNS_API=dns_ali \
  Ali_Key=xxx \
  Ali_Secret=yyy
```

其他 DNS 服务商可以参考 acme.sh 的 DNS API 文档：

<https://github.com/acmesh-official/acme.sh/wiki/dnsapi>

DNS API 的好处是不用开放 80 端口也能签发泛域名证书，比较适合家庭宽带和 NAS 场景。

## 启动整套服务

配置完成后启动：

```bash
ct-cntr up
```

它会根据已添加的容器、配置变量和依赖关系生成 Docker Compose 配置，然后启动对应服务。

后续升级一般只需要：

```bash
ct-cntr repo update
ct-cntr up
```

如果要更新工具本身：

```bash
python3 -m pip install -U linktools linktools-cntr
```

## 配置雷池 WAF

启动后，可以先重置雷池管理员密码：

```bash
ct-cntr exec safeline reset-admin
```

然后访问雷池控制台，例如：

```text
http://飞牛局域网IP:9200/
```

推荐先添加一个泛域名防护站点：

| 字段 | 值 |
|------|----|
| 域名 | `*` |
| HTTP 端口 | `8000` |
| HTTPS 端口 | 留空 |
| 上游服务器 | `http://nginx:8000` |

保存后开启攻击防护。

对于飞牛后台、SSO 后台这类敏感服务，可以单独添加站点并开启人机验证：

- **fnOS**（`fn.example.com`）：开启人机验证后，需配置 UA 排除规则，当 User-Agent **不包含** `com.trim.app` 且**不包含** `FNAppVer` 时才触发，避免误伤飞牛 App 端
- **SSO**（`sso.example.com`）：开启人机验证后，需配置 URL 路径排除规则，当请求路径**不以** `/api/` 开头且**不以** `/.well-known/` 开头时才触发，避免影响 OIDC 等接口的正常调用

## 配置 SSO 和二步验证

查看 Authelia / LLDAP 的初始配置：

```bash
ct-cntr config list authelia
```

找到 `AUTHELIA_LDAP_PASSWORD` 后，用 `admin` 账号登录：

```text
https://sso.example.com:3000/auth-admin/
```

首次绑定 OTP 或 WebAuthn 时，如果需要查看通知链接，可以执行：

```bash
ct-cntr exec authelia show-notification
```

建议创建自己的日常管理员账号，并同时加入以下两个组：
- `admins`：Authelia 管理员权限
- `lldap_admin`：LLDAP 控制台管理权限（缺少此组将无法登录 `/auth-admin/`）

后续接入 SSO 的管理服务，可以统一走 Authelia 做登录和二步验证。

## 免密登录：这才是 SSO 最香的地方

很多人以为 SSO 只是"统一登录入口"，但它真正省事的地方在于：**配置好之后，后端系统根本不需要再输密码。**

Authelia 支持多种对接协议，覆盖范围很广：

| 协议 | 适用系统 |
|------|---------|
| **OIDC**（OpenID Connect）| Portainer、Pve、gitlab、Nextcloud 等支持标准 OIDC 的应用 |
| **OAuth2** | 同上，很多现代应用两者都支持 |
| **Basic Authentication 代理** | OpenWrt LuCI等只有账号密码框的旧系统 |
| **API Key 注入** | Safeline等部分只支持 Token 认证的系统 |
| **Forward Auth** | 任何通过 nginx 反代的应用，无需应用本身改动 |

实际效果是：你在 Authelia 登录一次、通过二步验证之后，打开 Portainer、Safeline、PVE、OpenWrt，这些系统不用再次输入密码。  
一次验证，全套放行。

这对 Homelab 来说意义很大——管理类系统的密码往往各不相同、很难记，统一到 SSO 之后，既省去了重复输密码，又不影响安全性（二步验证还在）。

## 飞牛上的一个小建议：延迟启动 Docker

NAS 重启时，有时 Docker 会比数据盘挂载更早启动，导致容器目录不可用。  
可以给 Docker 增加一个短暂延迟：

```bash
SYSTEMD_EDITOR="vim" systemctl edit docker.service
```

添加：

```ini
[Service]
ExecStartPre=/bin/sleep 60
```

这样可以减少重启后容器异常的概率。

## 为什么我觉得这套方式适合飞牛

飞牛 OS 的优势是上手快、NAS 体验完整，Docker 也比较适合跑家庭服务。  
但 Homelab 真正长期使用时，关键不是“能不能跑起来”，而是：

- 能不能统一入口
- 能不能自动维护证书
- 能不能减少公网暴露风险
- 能不能快速恢复
- 能不能把配置沉淀下来
- 能不能未来继续扩展

`linktools-cntr` 正好补上了这部分能力。它把容器部署从“到处复制 compose 文件”变成“添加服务、设置变量、统一启动”的方式，比较适合飞牛这类长期运行的家庭服务器。

我个人比较喜欢的一点是：服务多了以后，配置仍然是可读、可查、可更新的。  
比如看配置：

```bash
ct-cntr config list
```

看最终 compose：

```bash
ct-cntr config
```

重启服务：

```bash
ct-cntr restart
```

这些命令都很直观，适合后续维护。

## 最终效果

最终访问体验大概是：

- 打开主域名，进入 Flare 导航页
- 通过 `fn.example.com` 访问飞牛
- 通过 `portainer.example.com` 管理容器
- 通过 `sso.example.com` 管理统一登录
- 公网入口前面有 WAF
- 证书自动申请和续期
- 后续新增服务继续通过 `ct-cntr add` 和 `ct-cntr up` 管理

这套方案不是为了把飞牛变复杂，而是为了让飞牛在服务变多以后仍然好维护。  
如果你也在用飞牛跑 Docker、反代、下载器、媒体库、开发环境或 Home Assistant，可以试试把入口和安全层统一起来，后面会省心很多。

项目文档里还有更完整的飞牛部署步骤和网络规划，可以按自己的网络环境调整：

<https://github.com/linktools-toolkit/linktools-homelab/blob/master/2xx-homelab/221-fnos/README.md>
