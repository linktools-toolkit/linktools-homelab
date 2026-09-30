# 数据库迁移

```bash
ct-cntr exec gitlab migrate-db --from-version 16
# 旧数据是 PostgreSQL 17 时使用 --from-version 17
```

命令拉取对应的旧版镜像和 `postgres:18-alpine`，停止 GitLab 和数据库，
然后运行两个临时容器：挂载旧数据执行 `pg_dumpall`，挂载新目录执行 `psql` 导入。
导入出错即停止，不会自动切换数据目录或启动 GitLab。

- 原数据：`APP_PATH/postgres`，保留不删除。
- 新数据：`APP_PATH/postgres-18/18/docker`。
- SQL 备份：日志显示的 `APP_PATH/postgres-backup-*/cluster.sql`，包含角色及密码哈希，请妥善保存。

成功后在部署主机手动切换（替换实际路径，并确保 `postgres-old` 不存在）：

```bash
sudo mv /实际APP_PATH/postgres /实际APP_PATH/postgres-old
sudo mv /实际APP_PATH/postgres-18 /实际APP_PATH/postgres
ct-cntr up gitlab
```

适用于本机 Docker 的默认 PostgreSQL 配置，要求数据库用户具有超级用户权限。
迁移期间暂停自动部署，避免服务或其他数据库写入方重新启动；空间需能容纳旧库、新库及导出文件。
自定义扩展、表空间、认证配置需要手动处理。新实例使用官方默认认证配置；旧 MD5 密码哈希需重设才能使用 SCRAM。
用于初始化的随机管理角色在完成后禁用登录。失败后保留导出及新目录排查，重新执行前须移走失败的 `postgres-18` 目录。

GitLab 官方兼容表目前未列出 PostgreSQL 18；正式启用前请核对
[所用 GitLab 版本的支持范围](https://docs.gitlab.com/install/requirements/#supported-versions)。
