# 开发者指南

## 开发边界

项目声明的产品树是产品面，默认是 `src/`，声明写在 `AGENTS.md` 的“三个平面”
和 `README.md` 的目录表；`.agents/` 是 coding agent 开发面；`README.md`、
`USER.md` 和本文是 human 面。一个主题只在一个权威位置展开，其他位置链接过去。
运行状态、日志、receipt 和临时产物进入当前 worktree 的 `.project/`，不进入
tracked source，也不写到未知的全局目录。

非代码产品树（例如论文的 `paper/`）同样自包含：只复制产品树本身就能构建，
不读取 `.agents/` 中的任何文件；构建输出和中间文件写入 `.project/`（例如
`.project/build/`），不写回产品树或仓库根目录。

## Issue、branch 和 PR

较大的工作单元先有 Issue，Issue 先收敛问题、范围、验收方式和风险，再开始实现。
小修小改可以直接在 `dev` checkout 里做，不建 Issue、worktree 或 PR；这类改动包括
文档、注释、memory/索引、拼写、单文件且没有设计决定的小修复，以及运行现有命令做
验收而不改产品代码。拿不准时按大的走；小改动变大或出现设计问题时停下来开 Issue。
小改动同样不自动提交或推送；运行适用的检查，并报告证据。

需要 Issue 的工作单元，从 `dev` 创建 `fix/issue-<N>-<slug>`、`feat/issue-<N>-<slug>`、
`docs/issue-<N>-<slug>` 或 `chore/issue-<N>-<slug>` branch。实现和验证完成后
提交 PR 回 `dev`；`main` 只承载已发布状态。

PR 描述应说明改了什么、为什么改、验收和 CI 要求的每项检查的命令与结果，以及
顺带修复的相关缺陷；只有维护者本人才能完成的步骤写成具体阻塞，说明维护者要做
什么。真实运行、构建和发布证据放在 Issue 或 PR 中，不靠 agent 的自述代替。

开始实现需要 Issue 的工作单元时，使用 Herdr 的原生 worktree 命令从 `dev` 创建
Issue branch，并在新 pane 启动独立的 coding-agent session。不要在当前 agent 窗口
直接 `git switch -c`。新 session 的第一步是运行 setup；父 session 可用下面的命令
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
记录；它不会自动删除 worktree。`setup-project.sh` 在 `.project/` 下创建的条目，
在 `.agents/scripts/migrate-project.rules` 里逐行写明迁移方式
（`NAME|ACTION|WHY`，ACTION 为 `copy`、`drop` 或 `login`），否则 teardown 会
停下来要求决定。确认资产已迁移、相关进程已停止、没有唯一副本
留在旧目录后，再用 worktree 管理工具销毁 worktree 和 branch。

## 环境变量与资产

`.env.example` 只声明变量名、用途和文件路径约定，不包含秘密。大资产放在
外部存储时，在仓库内的 `assets/` 登记稳定逻辑入口，并在 `assets/MANIFEST.yaml`
登记：用途、来源、版本、checksum、可重建性和删除 worktree 前的保留要求。
机器相关的软链接写在被忽略的 `.project/assets.links` 中，由 setup 创建；不要
提交软链接或其绝对目标路径。

## Memory 与 knowledge

`.agents/memory/` 记录长期决策，`.agents/knowledge/` 记录有来源和刷新条件的
事实。两个目录的 `AGENTS.md` 只包含规则和简短索引；正文按主题拆成独立 Markdown
文件，放入 `shared/` 或 `project/`，并使用对应的 `ENTRY_TEMPLATE.md` front
matter。新增或迁移条目时同步更新分组索引和 `content-registry.yaml`。

## 分支模型与仓库可见性

模板采用 `dev` 集成、`main` 发布的双分支模型。新仓库第一次 setup 会在可用的
GitHub CLI 环境中幂等创建并推送 `dev`，并把 GitHub 默认分支设为 `dev`；也可以
显式运行 `bash .agents/scripts/init-branches.sh`。诊断会报告缺失项和修复命令。

采用模板时优先选择 **Private**，直到产品、筛选记录和实验结果准备公开。公开前
检查凭据、私有数据、Issue/PR 内容、日志和本机路径；模板仓库本身是公开的，向它
提交的 Issue 会显示下游仓库名称和描述，因此模板反馈只能包含通用、脱敏的复现
信息，并只说明下游是私有还是公开仓库；仅当下游公开且其维护者同意时才写出仓库名称。

## 验证策略

测试只用于验证真实风险、历史缺陷和生产接缝。不为 coverage 机械增加测试。
产品完成至少需要经过适用的 public entrypoint、真实构建或运行路径；局部测试
通过不能替代产品验收。

```bash
bash .agents/scripts/diagnose-environment.sh
bash .agents/scripts/inspect-state.sh
```

## 产品构建与安装骨架

需要 Python 包、容器或安装入口的项目从根目录的 `pyproject.toml`、`Dockerfile`
和 `install.sh` 占位文件开始，替换项目名、依赖、基础镜像和 public entrypoint。
包清单只从产品树（默认 `src/`）收集产品代码；`.dockerignore` 排除 `.agents/`、
`.project/`、`AGENTS.md`、`CLAUDE.md` 和开发文档。非 Python、非代码或不需要镜像的
项目可以删除或改写对应骨架，并在 adoption/upgrade 迁移地图中记录取舍。

## 与模板的关系

本仓库是 `coding-agent-project-template` 的模板仓库本身；当前模板版本记录在
`.agents/content-registry.yaml` 的 `template.version`，模板自己的发布历史在
`RELEASE_NOTES.md`。

从模板创建的项目在自己的 registry 里记录它采用的 `template.repository` 与
`template.version`，并保留自己的 `RELEASE_NOTES.md`，不复制模板的发布历史。
升级到新的模板版本用 `.agents/skills/shared/template-upgrade/`；发现模板本身的
缺陷或缺失能力时用 `.agents/skills/shared/template-feedback/` 向上游开 Issue；
模板维护者主动收集下游已沉淀的通用实践用 `.agents/skills/template-harvest/`
（只属于模板仓库，下游不复制）。只有 URL 是项目专用的，其余规则通用。

派生模板是从本模板建立、自己又作为模板供其他项目使用的仓库，例如论文模板
[`paper-agent-project-template`](https://github.com/a-green-hand-jack/paper-agent-project-template)。
它的 registry 用 `template` 记录它自己和它自己的版本，并用 `template.upstream`
记录它所跟随的上游模板：

```yaml
template:
  repository: <派生模板自己的仓库 URL>
  version: <派生模板自己的 release tag>
  upstream:
    repository: https://github.com/a-green-hand-jack/coding-agent-project-template
    version: <它跟随的本模板 release tag>
```

| 仓库 | `template.repository` / `template.version` | `template.upstream` |
| --- | --- | --- |
| 本模板 | 本模板，当前模板版本 | 无 |
| 从本模板创建的项目 | 本模板，采用的 tag | 无 |
| 派生模板 | 派生模板自己，它自己的 release | 本模板和它跟随的 tag |
| 从派生模板创建的项目 | 派生模板，采用的 tag | 无 |

一个仓库跟随的模板是 `template.upstream`（有这一字段时），否则是 `template`
（本模板自身除外）。`template-adoption` 写入这一字段，`template-upgrade` 从它读取
升级的源版本并把它更新到目标 tag，`template-feedback` 用它把派生模板从上游继承的
缺陷路由到上游仓库。从派生模板创建的项目只记录该派生模板，删除复制来的
`upstream` 块；它的反馈先到派生模板，由派生模板判断是否转给上游。

## 发布

发布前检查：工作树干净、文档与行为一致、资产 manifest 可解析、环境入口可用、
适用的回归和真实运行证据已记录。运行
`.agents/skills/shared/release-doc-audit/`，处理或记录每个文档审计发现。发布只
从 `main` 或 release branch 进行，并更新下游项目自己的 `RELEASE_NOTES.md`；
模板仓库的 `RELEASE_NOTES.md` 只记录模板版本，不作为下游版本记录。

模板仓库发布前还要运行 `.agents/skills/template-harvest/`，收集下游已沉淀的通用
实践，并把每个候选的分类与 Issue 记录下来；没有可访问的下游时在发布记录中写明。
该 skill 只属于模板仓库，下游项目不复制，也不在自己的发布清单中引用。

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
- 不修改活动运行下的代码：代码修改和合并在另一个 worktree 进行；运行中的
  checkout 里的脚本必须替换时，先写新文件再 rename 覆盖，不原地编辑；向该
  checkout pull 或 merge 前先用 monitor 入口确认没有活动运行；
- 将实现完成、运行验收和最终产物验收分开报告。

通用原则和最小操作清单见 `.agents/skills/shared/cli-first-operations/` 与
`.agents/skills/shared/long-running-supervision/`。
