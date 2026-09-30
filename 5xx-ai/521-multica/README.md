# Multica CLI

```bash
# 添加 GitHub 仓库，按需选择工作区和项目
ct-cntr exec multica add-github https://github.com/owner/repo --ref main --label backend

# 选择并解除当前 daemon 的本地资源或项目共享的 GitHub 资源关联
ct-cntr exec multica remove-resource

# 额外包含其他 daemon 及没有 daemon 归属的本地资源
ct-cntr exec multica remove-resource --all-daemons

# 指定工作区、项目和资源，选定后仍需确认
ct-cntr exec multica remove-resource --workspace-id my-team --project-id backend --resource-id /workspace/backend
ct-cntr exec multica remove-resource --all-daemons --workspace-id my-team --project-id backend --resource-id RESOURCE_ID
```

`add-local`、`add-github`、`remove-resource` 都支持 `--workspace-id` 和 `--project-id`，沿用 `add-local` 的选择方式。
只有一个候选时自动选择；多个候选时交互选择，非交互环境必须提供足以唯一定位的参数。
`--resource-id` 支持 ID 前缀、完整标签、本地路径或仓库 URL；标签、路径和 URL 区分大小写。
删除命令只解除选中项目里的资源关联，不删除磁盘文件或远端仓库。
选定资源后会显示工作区、项目、资源类型、ID、标签及路径或 URL，要求二次确认，默认取消。
即使只有一个候选、指定了 `--resource-id` 或使用 `--all-daemons`，也必须确认；输入结束或禁用交互时不会自动删除。
本地资源默认仅允许选择 `resource_ref.daemon_id` 与当前 `MULTICA_DAEMON_ID` 一致的记录，
即使提供 `--resource-id` 也不能绕过过滤。`--all-daemons` 额外包含当前项目内其他 daemon 及无归属的本地资源。
GitHub 资源由项目共享，默认会出现在候选列表中，无需 `--all-daemons`。
解除 GitHub 资源关联影响整个项目，不是仅对当前 daemon 隐藏。
