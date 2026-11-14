# Release notes

## v0.1.37 — 2026-11-14

**memory 与 knowledge 只保留当前记录：过时记录连同文件删除，历史交给 Git。**

### `retention` 机制退出

registry 过去允许 memory/knowledge 记录以 `status: superseded|retired` + `retention: historical` + `retention_reason` 继续留在仓库，索引还会把它们标成 history。这与“仓库只呈现当前状态”冲突：过时记录继续出现在阅读路径上，索引生成与校验也长期为历史服务（#179）。

本版删除 `retention`、`retention_reason` 与 `historical_body()`：

| 情况 | 现在的行为 |
| --- | --- |
| 条目含 `retention`/`retention_reason` | `check-development.sh` 失败，提示删除该记录与文件、历史留在 Git |
| 条目为 `status: superseded` 或 `retired` | 同样失败，提示删除记录与文件 |
| 替换链指向已删除的身份 | 允许：引用保留为出处，不再报 dangling |
| 现存记录之间的替换环 | 仍然失败（`replacement cycle`） |
| 生成索引 | 只列 active 记录，不再出现 history 标注 |

`status: rejected` 仍是有效决定（未采纳的内容），保持不变。

### 升级时的行为

`upgrade-template.sh` 在升级时删除本地 `status: superseded|retired` 的条目及其文件，并在计划里报告 `removed with its <status> record; the history stays in Git`；保留条目上的 `retention*` 字段一并清掉。frontmatter 里的替换引用解析不到唯一身份时按原文保留，不再因此挂起整次升级；如果目标版本仍登记同一路径，命令按冲突拒绝并要求人工决定哪条记录是当前记录。

### 发布顺序

自 v0.1.36 起发布顺序固定为 **dev → main → tag → Release**：先在 `dev` 准备版本并跑本地门禁，再合并 `dev` 到 `main`，然后**在 `main` 的合并提交上**创建 annotated tag，最后发布 Release。绝不在 `dev` 或 worktree 分支上打 tag，也不先打 tag 再合并（`DEV.md`、`release-doc-audit`）。

### Upgrading a project from v0.1.36

**Command only.**

用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.37`。共享文件按常规规则替换，本地 `## In this repository` 段保留；升级会删除自身的 superseded/retired 记录与其文件并报告，因此升级后的 registry 能直接通过检查。手工维护的仓库若仍带 `retention*`，按检查器提示删除这些记录与文件后再发布。

### 验证与范围

本地门禁：`check-development.sh`（含索引一致）、`check-shells.sh` 通过，模板自有测试 167 项全部通过。新增用例覆盖：含 `retention` 或 superseded/retired 条目的 registry 失败并说明理由、删除记录与文件后通过、替换链在被替换者缺席时不报错、升级删除 superseded 记录并保留对它的引用、索引不再标注 history。本模板没有产品运行时，因此本版没有真实运行或构建面之外的验证。

### 参考

- 问题：[#179](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/179)
- PR：[#180](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/180)
- 来源：[paper-agent-project-template#225](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/225)、[paper-agent-project-template#230](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/230)
- [上一版 v0.1.36](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.36)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.36...v0.1.37)
