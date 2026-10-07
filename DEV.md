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

开始实现时，使用 Herdr 的原生 worktree 命令从 `dev` 创建 Issue branch，并在
新 pane 启动独立的 coding-agent session。不要在当前 agent 窗口直接
`git switch -c`。新 session 的第一步是运行 setup；父 session 可用下面的命令
生成包含 Issue 链接、分支、读取范围和验收要求的初始 prompt：

```bash
bash .agents/scripts/new-agent-prompt.sh 123 fix/issue-123-example
```

Herdr 不可用时应报告阻塞，不能改用当前窗口直接实现。

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
外部存储时，在仓库内的 `assets/` 登记稳定逻辑入口，并在 `assets/MANIFEST.yaml`
登记：用途、来源、版本、checksum、可重建性和删除 worktree 前的保留要求。
机器相关的软链接写在被忽略的 `.project/assets.links` 中，由 setup 创建；不要
提交软链接或其绝对目标路径。

## 分支模型与仓库可见性

模板采用 `dev` 集成、`main` 发布的双分支模型。新仓库第一次 setup 会在可用的
GitHub CLI 环境中幂等创建并推送 `dev`，并把 GitHub 默认分支设为 `dev`；也可以
显式运行 `bash .agents/scripts/init-branches.sh`。诊断会报告缺失项和修复命令。

采用模板时优先选择 **Private**，直到产品、筛选记录和实验结果准备公开。公开前
检查凭据、私有数据、Issue/PR 内容、日志和本机路径；模板仓库本身是公开的，向它
提交的 Issue 会显示下游仓库名称和描述，因此模板反馈只能包含通用、脱敏的复现
信息。

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

## CLI 与长时运行监督

项目的 setup、run、status、monitor、checkpoint、resume、artifact 和 release
操作应通过一个稳定的 public CLI 暴露。不要让 coding agent 或 human 通过私有
Python 函数、临时 provider SDK 或第二套脚本绕过产品入口。

如果产品运行时间超过一个交互回合：

- 在 `.project/runs/` 记录 worktree、状态根、配置、版本、输出目录和进程身份；
- 在独立的 Herdr pane、tmux 或 service 中运行，不占住 coding agent 的前台上下文；
- 提供一个只读 `status` 或 `monitor` 入口，展示进度、最后活动、错误、产物和恢复提示；
- 将结构化 receipt 和日志写进当前 worktree 的状态根；
- 明确定义 stop、checkpoint、resume、retry 和 terminal failure；
- 将实现完成、运行验收和最终产物验收分开报告。

通用原则和最小操作清单见 `.agents/skills/shared/cli-first-operations/` 与
`.agents/skills/shared/long-running-supervision/`。
