# 开发者指南

## 开发边界

`src/` 是产品面；`.agents/` 是 coding agent 开发面；`README.md`、`USER.md`
和本文是 human 面。一个主题只在一个权威位置展开，其他位置链接过去。
运行状态、日志、receipt 和临时产物进入当前 worktree 的 `.project/`，不进入
tracked source，也不写到未知的全局目录。

## Issue、branch 和 PR

每个工作单元先有 Issue，Issue 先收敛问题、范围、验收方式和风险，再开始实现。
从 `dev` 创建 `fix/issue-<N>-<slug>`、`feat/issue-<N>-<slug>`、
`docs/issue-<N>-<slug>` 或 `chore/issue-<N>-<slug>` branch。实现和验证完成后
提交 PR 回 `dev`；`main` 只承载已发布状态。

PR 描述应说明改了什么、为什么改、如何验证、哪些内容没有验证以及仍然存在的
风险。真实运行、构建和发布证据放在 Issue 或 PR 中，不靠 agent 的自述代替。

## Worktree 生命周期

每个 worktree 都是独立的工作单元，必须拥有自己的状态根、运行目录、输出目录
和资产入口。创建 worktree 后，在其中运行：

```bash
bash .agents/scripts/setup-worktree.sh
```

setup 会写入 `.project/home` 和 `.project/worktree.env`，创建本地状态目录，
检查工具和资产 manifest，并记录当前 branch、commit 和路径。不要手工复用另一个
worktree 的 `.project/`。具体项目可以提供可执行的
`.agents/scripts/setup-project.sh` hook；setup 会在基础初始化后调用它。

合并 PR 后不要直接删除目录。先运行：

```bash
bash .agents/scripts/teardown-worktree.sh --migrate-to /path/to/canonical-project
```

该命令会检查 ignored state、复制可保留的本地状态、保留资产软链接并写入迁移
记录；它不会自动删除 worktree。确认资产已迁移、相关进程已停止、没有唯一副本
留在旧目录后，再用 worktree 管理工具销毁 worktree 和 branch。

## 环境变量与资产

`.env.example` 只声明变量名、用途和文件路径约定，不包含秘密。大资产放在
外部存储时，在仓库内的 `assets/` 建立软链接，并在 `assets/MANIFEST.yaml`
登记：用途、来源、版本、checksum、可重建性和删除 worktree 前的保留要求。

## 验证策略

测试只用于验证真实风险、历史缺陷和生产接缝。不为 coverage 机械增加测试。
产品完成至少需要经过适用的 public entrypoint、真实构建或运行路径；局部测试
通过不能替代产品验收。

```bash
bash .agents/scripts/diagnose-environment.sh
bash .agents/scripts/inspect-state.sh
```

## 发布

发布前检查：工作树干净、文档与行为一致、资产 manifest 可解析、环境入口可用、
适用的回归和真实运行证据已记录。发布只从 `main` 或 release branch 进行，
并更新 `RELEASE_NOTES.md`。
