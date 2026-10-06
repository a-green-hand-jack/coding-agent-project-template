# Coding-Agent Project Template

这是一个面向 coding agent 的通用项目起点。它把项目分成三个平面：

- **产品面**：`src/`、正式配置、运行入口和发布产物；
- **开发面**：`AGENTS.md`、`.agents/`、worktree setup、状态和资产工具；
- **human 面**：`README.md`、`USER.md`、`DEV.md`、Issue、PR 和 release notes。

模板提供可复用的开发控制面：coding agent 可以自行读懂仓库，human 不需要反复
讲述上下文，每个 worktree 有自己的状态和环境，大资产有可见的仓库内入口，
Issue/branch/PR 构成可追溯的交付单元。

## 开始一个新项目

1. 在 GitHub 使用 **Use this template** 创建新仓库。
2. 修改本 README、`USER.md` 和 `DEV.md` 中的项目占位内容。
3. 在 `src/` 放入产品代码，在 `tests/` 放入有明确价值的检查。
4. 在每个 worktree 中运行：

   ```bash
   bash .agents/scripts/setup-worktree.sh
   ```

5. 让 coding agent 先读取 `AGENTS.md`、`.agents/README.md` 和当前 Issue，
   再开始修改。

## 目录

| 路径 | 归属 | 用途 |
| --- | --- | --- |
| `src/` | 产品面 | 唯一的产品实现入口 |
| `tests/` | 产品/开发交界 | 只放回归和接缝检查 |
| `assets/` | 产品输入 | 大资产的可见入口、软链接和 manifest |
| `.project/` | worktree 本地状态 | 运行记录、日志、receipt、临时产物；被 Git 忽略 |
| `.agents/` | coding agent 开发面 | memory、knowledge、skills、setup 和诊断 |
| `README.md` | human 面 | 产品定位和导航 |
| `USER.md` | human 面 | 用户安装、使用和故障处理 |
| `DEV.md` | human 面 | 开发、验证、发布和生命周期 |

## 边界

项目运行产生的状态不应悄悄写到仓库外的未知位置。状态可以位于 worktree
下的被忽略 `.project/`，但必须可见、可定位、可迁移。大型 dataset、model
checkpoint 和其他不适合进入 Git 的资产可以放在外部存储；仓库内必须保留
`assets/` 中的软链接和 `assets/MANIFEST.yaml`，说明来源、版本、checksum
和可重建性。凭据不进入仓库，只通过 `.env.example` 中声明的路径或变量注入。

项目讨论不属于模板产品。模板只保留已经收敛的规则、目录、脚本和占位文档。
