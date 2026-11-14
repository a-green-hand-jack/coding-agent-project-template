# Release notes

## v0.1.36 — 2026-11-14

**修复 v0.1.35 在一个仍带历史块的仓库上以“重复身份”拒绝升级的问题，并把发布顺序写成规则。**

### 重复身份不再导致整次升级失败

v0.1.35 的 `upgrade-template.sh` 不再回放迁移表，也不再读写 `local_legacy_inventory`。一个 schema 2 但本地仍带这些历史块的仓库（例如从 v0.4.6 起的论文）在升级时，本地路径派生的稳定身份与目标在另一个路径登记的同一身份会各写一条 entry，`relationship_errors` 报 `duplicate stable identity after migration`，文件与 registry 都停在 preflight（#177）。

本版在合并注册表后按稳定身份去重，目标路径优先：

| 合并后的情况 | 行为 |
| --- | --- |
| 同一 id 在本地旧路径与目标新路径各有一条，旧文件未改动 | 只保留目标路径的 entry，旧路径写入 `upstream_path`，旧文件随删除步骤移除 |
| 本地内容已改动、身份被 `supersedes`/`superseded_by` 引用，或 `local-<id>` 已占用 | 本地条目改名为 `local-<id>`（保留 `legacy_generated_id`），或按冲突拒绝并提示人工复核 |

同一版还修正了删除判断：路径已被记录的移动重映射时，删除步骤回退到别名指向的原始位置判断本地文件——一致则一并删除，改动则报冲突，不再报 `already removed` 而留下旧布局残留（#174）。

历史块（`legacy_inventory`、`local_legacy_inventory`、`migrations`）仍在升级时删除并报告，registry 只保留当前状态；升级下限仍是 `v0.1.34`。

### 发布顺序写进文档

v0.1.35 的 tag 曾直接打在 `dev` 的发布提交上，`main` 停在上一版。现在 `DEV.md` 的发布段与共享的 `release-doc-audit` 技能都写明：**dev → main → tag → Release**，先合并 `dev` 到 `main`，再在 `main` 的合并提交上创建 annotated tag，最后发布 Release；绝不在 `dev` 或任何 worktree 分支上打 tag，也不先打 tag 再合并。v0.1.35 的 tag 已通过把 `dev` 合进 `main` 修正，`8e7b82f` 现在是 `main` 的祖先。

### Upgrading a project from v0.1.35

**Command only.**

用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.36`。共享文件按常规规则替换，本地 `## In this repository` 段保留；不再回放迁移表，也不改动 `path_mappings`。若升级在身份合并处报冲突，按提示为相关身份补 `local-` 前缀或人工复核后再运行。

### 验证与范围

本地门禁：`check-development.sh`、`check-shells.sh` 通过，模板自有测试 168 项全部通过。新增回归测试从“带 `local_legacy_inventory` 的 schema 2 仓库”升级到本版，断言每个 `id` 只出现一次、旧条目改名为 `local-<id>`、历史块被删除、`check-development.sh` 通过；该测试在 v0.1.35 的命令上以同一个 `duplicate stable identity after migration` 失败。本模板没有产品运行时，因此本版没有真实运行或构建面之外的验证。

### 参考

- 问题：[#174](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/174)、[#177](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/177)
- PR：[#178](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/178)
- 来源：[paper-agent-project-template#235](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/235)
- [上一版 v0.1.35](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.35)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.35...v0.1.36)
