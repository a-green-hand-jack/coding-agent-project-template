# Coding Agent 工作规则

## 先读什么

开始工作前，先读本文件、`.agents/AGENTS.md`、相关 Issue，以及与任务直接相关
的 `.agents/memory/`、`.agents/knowledge/` 和 `.agents/skills/`。先理解现有
代码和边界，再决定是否需要修改。

`CLAUDE.md` 是本文件的软链接索引，供 Claude Code 从仓库根目录发现同一套规则；
修改规则只修改 `AGENTS.md`，不要把两份内容分叉。

## 三个平面

- 产品只放在项目声明的产品树和明确的产品资源目录里；本项目的产品树是 `src/`
  （模板默认），改用其他产品树的项目在这里和 `README.md` 的目录表中写明；
- coding agent 的规则、经验、脚本和诊断放在 `.agents/`；
- 用户和开发者说明放在根目录 human 文档。

非代码产品（例如论文的 `paper/`）遵守同样的规则：产品树自包含，不依赖
`.agents/`，构建输出和中间文件进入当前 worktree 的 `.project/`。不要把开发资料
复制进产品，也不要把产品行为只写在开发资料里。

## 工作方式

- 根据任务、用户意图、checkout 状态及并行活动选择直接在 `dev` 开发或隔离工作；
  工作规模本身不强制创建 worktree。先检查并保留无关改动和运行中的任务；按风险和
  用户要求分别决定 Issue、审阅和 PR，并执行相应验收；提交和推送仍需明确授权。
- 需要派出 Herdr worktree 时，事先请维护者确认本次 coding agent、具体模型和 thinking
  level 三项；已明确提供的选择不重复询问。未确认不得派遣或静默 fallback。
  使用 Herdr 原生 worktree 能力创建，运行 `bash .agents/scripts/shared/setup-worktree.sh`，
  并用 `bash .agents/scripts/shared/new-agent-prompt.sh <issue-number>` 生成交接。
  Herdr 不可用时报告，不用原始 Git 创建替代 worktree。
- issue agent 负责承接任务；多个 PR 的合并及 dev 与 worktree 的集成冲突由 dev 中的
  协调者处理。相关新 Issue 可以由原 agent 在原 session/worktree 承接，明确范围和交付。
- 先删掉不必要的规则，再考虑增加规则；
- 不为特定角色、任务或 benchmark 写特例；
- 不写与代码重复的长注释和文档；
- 不用 agent 私有 memory 代替项目级 memory；
- 先查 `.agents/content-registry.yaml`，区分 shared 内容和 project 内容；
- 不把状态、日志、receipt 或资产藏在项目外的未知目录；
- 运行操作使用项目自己的脚本和 CLI，不创建全局命令；
- 保留无关修改，不重置、覆盖或提交别人的工作；
- 除非用户明确要求，不提交或推送 Git。
- 对外可见的 Issue、PR、推送或发布写入前先检查仓库可见性；无论仓库公开还是
  私有，都不得写入凭据、私有数据、本机绝对路径或未经脱敏的日志。
- Issue、PR、评论和 human 文档使用 `.agents/content-registry.yaml` 的
  `writing.language` 声明的工作语言，Issue 正文以 `writing.issue_sections`
  的段落开头；没有声明时沿用各文件已有的语言。模板自带的共享文本（
  `## In this repository` 段以上的部分）保持模板的语言，不翻译。

## 上下文与状态

每个 worktree 必须先运行 `.agents/scripts/shared/setup-worktree.sh`。所有本地状态进入
该 worktree 的 `.project/`。外部大资产必须有仓库内 `assets/` 软链接和 manifest；
凭据只通过路径或运行时环境注入，绝不写入 Git、日志或 manifest；项目需要的凭据
只按名字登记在根目录的 `credentials.yaml`（见 `llm-credentials`）。

## 证据

测试、构建、真实运行和发布分别报告。测试通过不等于产品完成，agent 的最终消息
也不等于交付证据。发现与任务相关的缺陷时，先保留失败证据，再在当前工作单元
修复并重新验证。
