# Coding Agent 工作规则

## 先读什么

开始工作前，先读本文件、`.agents/AGENTS.md`、相关 Issue，以及与任务直接相关
的 `.agents/memory/`、`.agents/knowledge/` 和 `.agents/skills/`。先理解现有
代码和边界，再决定是否需要修改。

`CLAUDE.md` 是本文件的软链接索引，供 Claude Code 从仓库根目录发现同一套规则；
修改规则只修改 `AGENTS.md`，不要把两份内容分叉。

## 三个平面

- 产品代码只放在 `src/` 和明确的产品资源目录；
- coding agent 的规则、经验、脚本和诊断放在 `.agents/`；
- 用户和开发者说明放在根目录 human 文档。

不要把开发资料复制进产品，也不要把产品行为只写在开发资料里。

## 工作方式

- 先通过 Issue 收敛范围、设计和验收，再修改代码；
- 先删掉不必要的规则，再考虑增加规则；
- 不为特定角色、任务或 benchmark 写特例；
- 不写与代码重复的长注释和文档；
- 不用 agent 私有 memory 代替项目级 memory；
- 先查 `.agents/content-registry.yaml`，区分 shared 内容和 project 内容；
- 不把状态、日志、receipt 或资产藏在项目外的未知目录；
- 运行操作使用项目自己的脚本和 CLI，不创建全局命令；
- 保留无关修改，不重置、覆盖或提交别人的工作；
- 除非用户明确要求，不提交或推送 Git。

## 上下文与状态

每个 worktree 必须先运行 `.agents/scripts/setup-worktree.sh`。所有本地状态进入
该 worktree 的 `.project/`。外部大资产必须有仓库内 `assets/` 软链接和 manifest；
凭据只通过路径或运行时环境注入，绝不写入 Git、日志或 manifest。

## 证据

测试、构建、真实运行和发布分别报告。测试通过不等于产品完成，agent 的最终消息
也不等于交付证据。发现与任务相关的缺陷时，先保留失败证据，再在当前工作单元
修复并重新验证。
