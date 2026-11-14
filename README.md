# Coding-Agent Project Template

这是一个面向 coding agent 的通用项目起点：agent 从仓库本身读懂规则、当前状态和下一步，
human 不必反复讲述上下文。它交付可复用、可升级的规则、skills、脚本和产品骨架。

项目分成三个平面：

- **产品面**：项目声明的产品树（默认 `src/`）、正式配置、运行入口和发布产物；
- **开发面**：`AGENTS.md`、`.agents/`、worktree setup、状态和资产工具；
- **human 面**：`README.md`、`USER.md`、`DEV.md`、Issue、PR 和 release notes。

模板不定义下游产品的领域模型，不规定评测、实验或论文的通用目录，也不提供第二套
调度器。采用模板前先明确自己的用户、交付物、核心概念和非目标，再按这些概念组织
产品；已有测试不因采用模板而统一搬迁。

## 快速开始

前置条件：Git；`gh` 已登录，仓库已有 `origin`（在 `main` 上首次运行 setup 会幂等
创建并推送 `dev`，把 GitHub 默认分支设为 `dev`，见 `DEV.md` 的“分支模型与仓库可见性”）；
检查命令需要 Python 3 和 PyYAML、markdown-it-py（`.project/venv` 或 `AGENTS_PYTHON`
指定的解释器，见下面“这个项目怎么跑”里的验证命令）。

```bash
bash .agents/scripts/shared/setup-worktree.sh   # 每个 worktree 一次
bash .agents/scripts/shared/check-development.sh
bash .agents/scripts/shared/check-shells.sh
```

在 `main` 上首次 setup 已经处理分支模型；只有需要改分支名、补推 `dev` 或更换 remote 时
才手工运行 `bash .agents/scripts/shared/init-branches.sh`。`diagnose-environment.sh` 报告
缺失的工具和修复命令。

## 这个项目怎么跑

产品树是 `src/`：产品代码、正式配置和 public entrypoint 都放在这里，包清单只从这里
收集。现在树里只有 `src/.gitkeep`；放入产品后，把上面的检查命令换成产品的 run/build
命令，并在 `USER.md` 写用户入口、配置和故障处理。

根目录有三个可选骨架。需要时替换成真的，不需要时删除，并在 adoption/upgrade 的迁移
地图记录取舍：

| 骨架 | 换成什么 |
| --- | --- |
| `pyproject.toml` | 项目名、依赖和 `src/` 下的包名；保留 `dev` extra 里的检查依赖 |
| `Dockerfile` | 基础镜像、依赖安装和产品 public entrypoint 的 `CMD` |
| `install.sh` | 产品支持的安装策略和解释器选择 |

`.dockerignore` 默认排除 `.agents/`、`.project/`、`AGENTS.md`、`CLAUDE.md` 和开发文档，
避免 coding-agent 开发面进入产品产物。

运行产生的状态不写回产品树或仓库根目录：日志、receipt、构建产物和临时文件进入被
Git 忽略的 `.project/`（`state/`、`runs/`、`artifacts/`、`manifest/`）。“验证与检查”
命令如下，模板自带测试只有模板仓库才跑：

```bash
bash .agents/scripts/shared/check-development.sh   # registry、链接、skill 前置段和索引
bash .agents/scripts/shared/check-shells.sh        # .agents/ 下 Shell 语法
.project/venv/bin/python -m unittest discover -s .agents/tests/project -p 'test_template_*.py'
```

检查器以隔离模式运行 Python，依赖装进 `.project/venv`，或用 `AGENTS_PYTHON` 指向已装
PyYAML、markdown-it-py 的解释器；细节见 `DEV.md` 的“验证策略”。

## 目录

| 路径 | 归属 | 用途 |
| --- | --- | --- |
| `src/` | 产品面 | 默认的产品树，产品代码、配置和入口的唯一来源 |
| `pyproject.toml` | 产品面 | 可选的 Python 包清单，占位元数据和 `src/` 包边界 |
| `Dockerfile` | 产品面 | 可选的容器构建入口，占位运行命令 |
| `install.sh` | 产品面 | 可选的安装入口，占位安装策略 |
| `.dockerignore` | 产品面 | 容器构建上下文边界，排除开发面 |
| `assets/` | 产品输入 | 大资产的稳定逻辑入口和 manifest；机器相关软链接在 `.project/` |
| `.project/` | worktree 本地状态 | 运行记录、日志、receipt、临时产物；被 Git 忽略 |
| `.agents/` | coding agent 开发面 | execution、tests、memory、knowledge、skills、scripts，各分 shared/project |
| `AGENTS.md` | coding agent 入口 | 三个平面、规则链和上下文约定；各级目录的 `AGENTS.md` 补充本级规则 |
| `CLAUDE.md` | coding agent 入口 | 指向 `AGENTS.md` 的 Claude Code 软链接 |
| `README.md` | human 面 | 产品定位、快速开始、目录和边界 |
| `USER.md` | human 面 | 用户安装、使用和故障处理 |
| `DEV.md` | human 面 | 开发、验证、分支模型、发布和生命周期 |
| `RELEASE_NOTES.md` | human 面 | 当前版本的说明和 `## Starting from this template` 起步手续 |
| `.env.example` | 配置约定 | 产品读取的变量名、用途和文件路径；不含凭据值 |
| `.github/` | 托管配置 | Issue/PR 模板和可选的 `template-check.yml`；不用托管 CI 时删掉 workflow |
| `.gitignore` | 忽略规则 | 忽略 `.project/`、虚拟环境和构建缓存 |
| `RELEASE_EXAMPLE.md` | 模板示例 | 图文发布草稿样例；下游不复制 |
| `DEVELOPMENT_WRITING_EXAMPLE.md` | 模板示例 | Issue、PR、评论和 commit 消息的中文正反例；下游不复制 |

## 边界

项目运行产生的状态不写进仓库外的未知位置：状态位于 worktree 下被忽略的 `.project/`，
必须可见、可定位、可迁移。大资产放在外部存储；仓库内保留 `assets/MANIFEST.yaml` 的
稳定条目，机器相关软链接由 setup 写入被忽略的 `.project/assets.links`，并说明来源、
版本、checksum 和可重建性。

凭据不进入仓库。采用模板后由 `llm-credentials` 建立根目录的 `credentials.yaml`，项目
需要哪些凭据只按名字登记在那里；值只通过 `.project/credentials/` 中指向设备共享文件
的链接或运行时环境注入，探测时只打印状态行。本模板自身不调用 LLM，所以没有这个文件。
格式见 `.agents/knowledge/shared/credential-inventory.md`，步骤见 `credential-setup` 技能。

非代码产品树（例如论文的 `paper/`）同样自包含：不依赖 `.agents/`，构建输出和中间文件
进入 `.project/`，不写回产品树或仓库根目录。

`.agents/content-registry.yaml` 登记哪些内容可以跨项目复用、哪些内容必须在新项目中重新
建立，以及每项复用需要怎样适配；六类目录和 schema 见 `.agents/AGENTS.md`，分组索引由
registry 生成。

## 分支模型与可见性

模板采用 `dev` 集成、`main` 发布的双分支模型：工作分支从 `dev` 开始，发布才合并到
`main`；需要联合验收的父任务可以按 `DEV.md` 声明集成分支，最终仍交付到 `dev`。

采用模板时优先选择 **Private**，直到产品、筛选记录和实验结果准备公开。公开前检查
凭据、私有数据、Issue/PR 内容、日志和本机路径；模板仓库本身是公开的，向它反馈时不要
放入下游私有内容。完整规则见 `DEV.md` 的“分支模型与仓库可见性”，
`diagnose-environment.sh` 报告当前仓库的可见性和默认分支。

## 论文项目

写论文从派生模板
[`paper-agent-project-template`](https://github.com/a-green-hand-jack/paper-agent-project-template)
开始，不从本模板开始：它的产品树是自包含的 `paper/`，并在自己的 registry 里用
`template.upstream` 记录跟随的本模板版本。从它创建的论文项目只记录该论文模板，按它
自己的 README 开始。派生模板与上游的关系见 `DEV.md` 的“与模板的关系”。

## 发布

发布顺序固定为 **dev → main → tag → Release**：在 `dev` 准备版本并跑本地检查，合并到
`main`，在 `main` 的合并提交上创建 annotated tag，再发布 Release。当前版本的说明在
`RELEASE_NOTES.md`；受众、正文和审计按 `DEV.md` 的“发布”与 `release-doc-audit` 技能。

## 来源

本仓库是 [coding-agent-project-template](https://github.com/a-green-hand-jack/coding-agent-project-template)
的模板仓库本身。采用模板时的起步手续（Use this template 或克隆 release tag、运行 setup、
填写占位内容、删掉模板专用内容、让 agent 读 `AGENTS.md`）在 `RELEASE_NOTES.md` 的
`## Starting from this template` 一节；升级与缺陷反馈分别交给 `template-upgrade`、
`template-feedback` 技能。采用模板后，删掉本节和那一节。
