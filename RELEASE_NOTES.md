# Release notes

本文件只描述当前发布；历史版本保留在各自的标签里（例如 `git show v0.1.40:RELEASE_NOTES.md`）。
基于本模板创建的项目维护自己的发布说明，不复制此历史。

## v0.1.41 — 2026-11-24

仓库的 Issue/PR 表单从现在起是**可 review 的项目文件**：模板改了表单，升级计划会把改动
给你看，而不是悄悄跳过；下游给模板报问题也有了自己的表单。写作规范的权威写清了一处：
registry 的 `issue_sections` 决定 Issue 正文的段落，表单字段只是提示。

- **表单不再是静默冻结的文件。** `.github/ISSUE_TEMPLATE/{bug,feature}.yml` 与
  `.github/PULL_REQUEST_TEMPLATE.md` 仍属项目所有（`scope: project`），但登记为
  `upgrade: review`：模板改动它们时，升级计划打印本版 diff，由项目决定是否合并。此前这类
  改动从不进入采用者——抽查的两个采用者，其表单分别停在模板 v0.1.13 与 v0.1.26，之后的
  改进一次都没到过。模板新增而项目没有的可 review 文件，计划写成
  `new here (upgrade: review); adopt it with git -C … show <tag>:<path> if it fits, or leave it out`，
  不会写入。
- **下游反馈有了专用表单。** 新增 `.github/ISSUE_TEMPLATE/template-feedback.yml`：模板版本
  与下游类型、复现、期望与观察、为什么是跨项目问题、提案、兼容/迁移/清理影响，以及公开
  仓库的边界（不含凭据、私有内容、本机路径、原始日志）。`template-feedback` 指向它，并
  首次写明 PR 通道：只用于已被 Issue 覆盖的改动或显而易见的机械修复，行为改变与新规则仍
  先开 Issue。该文件登记为 `optional: true`，项目可以采纳或不用。
- **权威写清。** `issue-workflow` 的 Writing conventions 现在说明：`issue_sections` 决定
  Issue 正文开头的段落顺序，表单字段不构成第二套顺序；采用者把自己的表单映射到自己的段落。
- **采用步骤补上表单。** `template-adoption` 增加一步：采用时把模板的 Issue/PR 表单落成
  自己的文件、字段映射到自己的段落（或记录不采用），并说明此后模板改动只以 review diff 到达。

采用者这次升级会看到什么：

| 计划里出现 | 含义 | 要做什么 |
| --- | --- | --- |
| `Review` 里有 `.github/...` | 模板改了这一版的形式或内容，文件仍归你所有 | 看 diff，决定合并进自己的表单还是保持现状 |
| `Manual` 里有 `new optional content … template-feedback.yml` | 新增的反馈表单是可选的 | 想用就 `git show <tag>:.github/ISSUE_TEMPLATE/template-feedback.yml` 取来，或留着不用 |
| `Refused`（若之前内联改过共享脚本） | 本地补丁与新版共享脚本冲突 | 把补丁移进项目文件（`.agents/scripts/project/`），见 v0.1.40 的说明 |

### 升级时的行为

共享 skill 与 `upgrade-template.sh` 按常规替换；表单属项目，只在 Review 里出现。本版没有
schema、布局或 registry 字段的变化。

### Upgrading a project from v0.1.40

1. 用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.41`。
2. 看 Review 列表里的 `.github` 条目：模板对表单的改动从本版起以 review diff 出现，采纳与否由项目决定。
3. 需要反馈表单的项目按 Manual 里的提示取用 `template-feedback.yml`，不需要就留着不用。
4. 运行 `bash .agents/scripts/shared/check-development.sh` 与本项目的检查命令。

### 验证与范围

本地检查：`check-development.sh` 通过（125 条登记）、`check-shells.sh` 通过（11 个文件）、
模板自有测试 176 项全部通过，其中本版新增 2 项、更新 1 项：项目改写过的表单被 review 且
不被写入（该 review 机制本版之前就有，这项守护的是新登记不被写坏）；模板新增而项目缺失的
可 review 文件按“new here”提示、不写文件、registry 条目保持 optional——去掉
`upgrade-template.sh` 的改动后这项失败，旧措辞会把项目根本没有的文件说成“项目自己的”。
CI 在 PR 上通过。

发布前下游风险检查（只读）：16 个在册采用者都有这三个表单，唯一的例外是还没有 registry 的
`research-funding-os`；因此本版不会让在册采用者出现 dangling entry。没有执行下游测试，也没有
在浏览器里核对 GitHub 的表单渲染（YAML 结构与字段 id 唯一性已用解析器检查）。

### 参考

- 问题：[#195](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/195)
- PR：[#196](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/196)
- 前序版本：[v0.1.40](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.40)（本地已有块不再重复插入、teardown 项目钩子、worktree 路径）
- [版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.40...v0.1.41)

## Starting from this template

1. 在 GitHub 使用 **Use this template** 创建新仓库，并优先选择 **Private**；需要可复现的
   起点时，克隆一个 release tag（把 `<TEMPLATE_TAG>` 换成 Releases 页上的目标 tag，不要用
   默认分支的浮动内容）：

   ```bash
   git clone --branch <TEMPLATE_TAG> \
     https://github.com/a-green-hand-jack/coding-agent-project-template.git my-project
   cd my-project
   git switch -c main
   git remote remove origin
   git remote add origin https://github.com/OWNER/PROJECT.git
   git push -u origin main
   ```

   不要用 `--depth 1`：浅克隆的仓库不能推送。

2. 在 `.agents/content-registry.yaml` 的 `writing:` 写本项目的工作语言和 Issue 开头段落，
   或删掉这一块（不声明）。
3. 首推前定下托管 CI，也就是 `issue-workflow` 的 `<CI>` 槽位，三选一：`no` 删掉
   `.github/workflows/template-check.yml`；`yes` 保留并确认本仓库的 Actions 能启动；
   `adopted-but-unavailable` 保留文件但用 `gh workflow disable template-check.yml` 停掉
   跑不起来的运行（按量计费或额度用尽时，每次推送都会留下一个从未启动的红色运行），
   Actions 恢复后 `gh workflow enable template-check.yml`。不论哪种，合并门槛都是本地检查。
   不用等 adoption 清理完成再推：复制出来的仓库里，模板自己的测试中依赖模板 release
   历史的那几项会自行跳过，首推拿到的是真实结果。
4. 运行 `bash .agents/scripts/shared/setup-worktree.sh`：它建立 `.project/`；在 `main` 上
   运行时还会幂等创建、推送 `dev`，并把 GitHub 默认分支设为 `dev`。在其它分支上或需要
   换 remote 时，手工运行 `bash .agents/scripts/shared/init-branches.sh`。工作分支从 `dev`
   开始，发布才合并到 `main`。
5. 修改 `README.md`、`USER.md` 中的项目占位内容；`DEV.md` 保留时一并改（v0.1.35 起
   下游可以删除它）。产品树不是 `src/` 时，在 `AGENTS.md` 的“三个平面”和 `README.md`
   的目录表中写明。
6. 删掉模板专用内容：registry 标 `scope: template` 的文件、本文档里的模板发布历史和这一节，
   换成项目自己的发布说明。
7. 让 coding agent 先读取 `AGENTS.md`、`.agents/AGENTS.md` 和当前 Issue，再开始修改；
   完整采用流程由 `template-adoption` 技能执行。

模板升级：`bash .agents/scripts/shared/upgrade-template.sh --check <TEMPLATE_TAG>` 输出计划，
去掉 `--check` 应用；跨过的每个版本都是 **Command only.** 且没有冲突时，一条命令加项目
检查就完成升级，否则按 `.agents/skills/shared/template-upgrade/` 走完整流程。跨项目反馈
按 `.agents/skills/shared/template-feedback/` 向模板仓库提 Issue。
