# Coding-Agent Project Template

这是一个面向 coding agent 的通用项目起点。它把项目分成三个平面：

- **产品面**：`src/`、正式配置、运行入口和发布产物；
- **开发面**：`AGENTS.md`、`.agents/`、worktree setup、状态和资产工具；
- **human 面**：`README.md`、`USER.md`、`DEV.md`、Issue、PR 和 release notes。

模板提供可复用的开发控制面：coding agent 可以自行读懂仓库，human 不需要反复
讲述上下文，每个 worktree 有自己的状态和环境，大资产有可见的仓库内入口，
Issue/branch/PR 构成可追溯的交付单元。

## 开始一个新项目

1. 在 GitHub 使用 **Use this template** 创建新仓库，并优先选择 **Private**。
2. 在新仓库运行 `bash .agents/scripts/init-branches.sh`，建立 `dev`、推送它并
   将 GitHub 默认分支设为 `dev`；之后 Issue branch 从 `dev` 创建，发布才合并
   到 `main`。
3. 修改本 README、`USER.md` 和 `DEV.md` 中的项目占位内容。
4. 在 `src/` 放入产品代码，在 `tests/` 放入有明确价值的检查。
5. 在每个 worktree 中运行：

   ```bash
   bash .agents/scripts/setup-worktree.sh
   ```

6. 让 coding agent 先读取 `AGENTS.md`、`.agents/AGENTS.md` 和当前 Issue，
   再开始修改。

### 可见性与公开边界

Private 是默认建议：Issue 中的候选筛选、实验结果、日志和路径通常先留在私有
仓库。决定公开前，确认没有凭据、私有数据、本机绝对路径或未经脱敏的日志，并
检查所有 Issue、PR 和发布说明。模板仓库是公开的，向模板仓库反馈时不要放入
下游私有内容；只保留必要的通用复现信息。仓库可见性与默认分支可用
`bash .agents/scripts/diagnose-environment.sh` 检查。

## 目录

| 路径 | 归属 | 用途 |
| --- | --- | --- |
| `src/` | 产品面 | 唯一的产品实现入口 |
| `pyproject.toml` | 产品面 | 可选的 Python 包清单，占位元数据和 `src/` 包边界 |
| `Dockerfile` | 产品面 | 可选的容器构建入口，占位运行命令 |
| `install.sh` | 产品面 | 可选的安装入口，占位安装策略 |
| `.dockerignore` | 产品面 | 容器构建上下文边界，排除开发面 |
| `tests/` | 产品/开发交界 | 只放回归和接缝检查 |
| `assets/` | 产品输入 | 大资产的稳定逻辑入口和 manifest；机器相关软链接在 `.project/` |
| `.project/` | worktree 本地状态 | 运行记录、日志、receipt、临时产物；被 Git 忽略 |
| `.agents/` | coding agent 开发面 | memory、knowledge、skills、setup 和诊断 |
| `CLAUDE.md` | coding agent 入口 | 指向 `AGENTS.md` 的 Claude Code 软链接 |
| `README.md` | human 面 | 产品定位和导航 |
| `USER.md` | human 面 | 用户安装、使用和故障处理 |
| `DEV.md` | human 面 | 开发、验证、发布和生命周期 |

## 边界

项目运行产生的状态不应悄悄写到仓库外的未知位置。状态可以位于 worktree
下的被忽略 `.project/`，但必须可见、可定位、可迁移。大型 dataset、model
checkpoint 和其他不适合进入 Git 的资产可以放在外部存储；仓库内必须保留
`assets/MANIFEST.yaml` 的稳定条目，机器相关软链接放入被忽略的
`.project/assets.links`，说明来源、版本、checksum
和可重建性。凭据不进入仓库，只通过 `.env.example` 中声明的路径或变量注入。

项目讨论不属于模板产品。模板只保留已经收敛的规则、目录、脚本和占位文档。

发布骨架是可选的，模板不绑定 Python、容器或发布渠道。需要这些入口的项目应
替换根目录的 `pyproject.toml`、`Dockerfile` 和 `install.sh` 占位内容，并保持包
清单只从 `src/` 收集产品代码；`.dockerignore` 默认排除 `.agents/`、`.project/`、
`AGENTS.md`、`CLAUDE.md` 和开发文档，避免 coding-agent 开发面进入产品产物。

`.agents/content-registry.yaml` 登记哪些内容可以跨项目复用、哪些内容必须在新
项目中重新建立，以及每项复用需要怎样适配。不要把项目专属 memory、knowledge
或 skill 当作通用资产整目录复制。

## 使用模板版本

GitHub 的 **Use this template** 使用默认分支上的最新模板。需要可复现的版本时，
从 release tag 创建起点：

```bash
git clone --branch v0.1.0 --depth 1 \
  https://github.com/a-green-hand-jack/coding-agent-project-template.git my-project
cd my-project
git remote remove origin
git remote add origin https://github.com/OWNER/PROJECT.git
git push -u origin main
```

使用某个模板版本后，先阅读模板仓库对应 tag 中的 `RELEASE_NOTES.md`；下游项目
应维护自己的 `RELEASE_NOTES.md`，不要把模板发布历史拷入下游。跨项目反馈请按
`.agents/skills/shared/template-feedback/` 的流程向模板仓库提 Issue。
