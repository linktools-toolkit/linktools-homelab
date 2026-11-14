# CloudCLI

CloudCLI 在 VS Code 的 `code-server` 容器内作为后台服务运行，通过独立域名访问。
它与 VS Code、Multica 共用项目目录、CLI 工具和 AI 登录配置，网页仍保持独立。

```sh
ct-cntr add cloudcli
ct-cntr config set CLOUD_CLI_DOMAIN=cloudcli.example.com
ct-cntr up vscode nginx
```

`cloudcli` 依赖 `vscode`，自身不再创建 Docker 服务。启动、更新或重启进程时需要显式选择 `vscode`；修改域名时还需选择 `nginx`。如需更新 Flare 导航，再显式选择 `flare`。

启动脚本在容器内从 npm 安装官方包 `@cloudcli-ai/cloudcli`（始终 latest），连同 `task-master-ai` 和 `cursor-agent` 一起装进持久化的 `/workspace/.node_modules` 与 `/workspace/.local`，容器重建后无需重新下载。npm 安装的原生依赖直接针对 code-server 内置 Node 编译，无需镜像内预构建。注意：官方 npm 包的前端未启用平台模式，首次访问需通过页面完成一次初始账号设置（单用户）；服务端仍以平台模式运行。

`.github/docker/cloudcli` 的镜像构建流水线已不再被部署依赖，仅作为带平台模式前端的备用构建保留。

nginx 将 `CLOUD_CLI_DOMAIN` 转发到 `code-server:3001`，继续使用原有访问控制。`CLOUD_CLI_PORT` 默认 `0`，只通过域名访问即可；设为正数时，该宿主机端口映射到 code-server 中的 CloudCLI。

CloudCLI 数据继续使用原来的 `cloudcli/home/.cloudcli` 宿主机目录，并挂载到 `/workspace/.cloudcli`，数据库仍为 `auth/cloudcli.db`。迁移前先停止旧的独立 CloudCLI 容器，避免两个进程同时使用数据库；旧容器停止后可手动移除，保留数据目录。仅原来 CloudCLI 独立 home 中的其他文件不会自动迁移，需要的文件请迁入 VS Code 的 home；共享项目和 AI 配置继续使用原有挂载。

新增或移除 CloudCLI 集成后，重启 `vscode` 即可生效（启动脚本挂载变化，镜像内容不再变化）。
