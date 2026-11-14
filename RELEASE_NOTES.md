# Release notes

## v0.1.34 — 2026-11-13

**跟随派生模板的下游升级时，不再得到同一身份的两条省略记录。**

v0.1.33 把 `omitted:` 定为“未采纳”的唯一记录，派生模板升级到 v0.1.33 后，其 registry 会自带省略记录（例如把缺文件的 optional 条目 `Dockerfile`、`pyproject.toml`、`install.sh`、`.dockerignore` 改记为省略）。跟随这个派生模板的下游若对同一身份已有自己的省略记录、理由不同，v0.1.33 的升级命令会按整条记录比较，把本地与目标的两条都保留下来；随后 `check-development.sh` 报 `duplicate omission`，即升级命令写出了自己的检查器拒绝的 registry。

本版按身份合并省略记录：id 相同或 path 相同视为同一条，本地记录及其理由优先，目标记录只补本地没有的身份。其余写入省略记录的位置（模板专属内容、缺文件 optional 条目的迁移）也按同一身份判断。

| 下游状态（目标只把该身份记为省略） | 升级结果 | 计划中的一行 |
| --- | --- | --- |
| 本地有理由不同的省略记录 | 只保留本地记录及理由 | 无 |
| 本地 active 条目 + 本地省略，文件不存在 | 移除条目，保留本地省略 | `kept out: <path> (omitted locally)` |
| 本地只有过时的 active 条目，文件不存在 | 移除条目，采用目标的省略记录 | `kept out: <path> (omitted in <target>)` |
| 本地没有任何记录 | 采用目标的省略记录 | 无 |

只影响跟随派生模板（目标 registry 自带 `omitted:`）的下游；直接跟随本模板的项目行为不变。

### Upgrading a project from v0.1.33

1. 派生模板：先把本版 `.agents/scripts/shared/upgrade-template.sh` 同步进来（可逐字节替换），再发布自己的下一版；否则跟随它的下游仍会用旧命令得到重复的省略记录。
2. 下游：使用目标版本完整的 `.agents/scripts/shared/` 命令目录执行 `upgrade-template.sh --check <TARGET_TAG>`，审阅 `kept out` 行后执行升级，并运行项目自己的检查。已因 v0.1.33 命令出现重复省略记录的 registry，用本版命令重跑一次升级即合并为一条，保留本地理由。

### 验证与范围

验收夹具以“目标 registry 带 `omitted`”的候选版本（派生模板作为目标）从真实 v0.1.33 升级，覆盖上表四种情况，断言升级后无重复、本地理由保留、`check-development.sh` 通过、重复升级字节不变。前两种情况在 v0.1.33 的命令上失败于 `duplicate omission`，后两种在 v0.1.33 上已正确，作为回归保护。来源是派生模板同步 v0.1.33 时的论文级回归测试；本版没有运行派生模板或下游项目。

### 参考

- [问题 #159](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/159)；来源 [paper-agent-project-template#218](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/218)；[上一版 v0.1.33](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.33)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.33...v0.1.34)。
