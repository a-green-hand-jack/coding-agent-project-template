# Release notes

本文件只描述当前发布；历史版本保留在各自的标签里（例如 `git show v0.1.41:RELEASE_NOTES.md`）。
基于本模板创建的项目维护自己的发布说明，不复制此历史。

## v0.1.42 — 2026-11-24

两个来自同一个私有下游仓库的报告，在同一处收口：**从模板复制出来的仓库，首推就该拿到
真实可信的 CI 结果**。一个是模板自有测试要求只有模板才有的 release tag（#198），另一个是
按量计费跑不起来时每次推送都留下一个看不出原因的红色运行（#199）。

- **发布比较按归属判断，而不是按 tag 数量。** 模板自有测试现在只在“这就是模板仓库”时
  比较发布（`origin` 与 registry 的 `template.repository` 一致），并且只认“自己的 registry
  声明了这个版本”的 tag。模板仓库里缺 tag **仍然失败**；复制出来的仓库里这些比较 skip，
  并打印需要的 `git fetch --tags` 命令。实测一次复制品：180 项中 39 项 skip、0 项失败，
  而改动前正是这 39 项把首推判红。
- **workflow 容忍取不到 tag。** `git fetch --depth=1 origin '+refs/tags/*:refs/tags/*'` 在
  origin 没有任何 tag 时静默退出 1（git 2.56 实测，无 stderr），所以只改测试不够。现在它会
  打印 `no tag on origin yet: the template release comparisons skip` 并继续。
- **托管 CI 跑不起来是可记录的状态。** `issue-workflow` 的 `<CI>` 新增
  `adopted-but-unavailable`：保留 workflow，用 `gh workflow disable template-check.yml`
  让推送不再产生从未启动的运行，Actions 恢复后 `gh workflow enable template-check.yml`
  即可，本地检查始终是合并门槛。
- **诊断直接指出这件事。** `diagnose-environment.sh` 读最近一次 `template-check.yml` 运行：
  没有任何 job 就说明托管 CI 没跑起来，并打印上面的命令与该槽位值；job 失败则指向
  `gh run view <id> --log-failed`；`gh` 不可用、未认证或没有运行记录时跳过，且从不因为这条
  检查失败。
- **起步手续先定 CI。** `## Starting from this template` 第 3 步把首推前的三选一写清
  （`no` 删文件 / `yes` 确认 Actions 可用 / `adopted-but-unavailable` 停掉跑不起来的运行），
  并说明不必等 adoption 清理完成才推。

### 升级时的行为

三个共享文件（`diagnose-environment.sh`、`issue-workflow`、`template-adoption`）按常规替换，
其余是模板自有内容。

一个必须说清的边界：#198 的修复**不会通过升级**到达“原样拷贝、尚未采用”的仓库——这些测试
登记为 `scope: template`，升级恰好跳过这一范围。这类仓库要么重新拷贝
`.agents/tests/project/test_template_support.py` 与 `test_template_fresh_copy.py` 及两处
改动，要么按 `template-adoption` 完成采用（它本来就会删掉模板自有测试）。已完成采用的项目
本来就没有这些测试，不受影响。

### Upgrading a project from v0.1.41

**Command only.**

升级后 `diagnose-environment.sh` 会多一行“最近一次 template-check 运行”；`<CI>` 槽位多了
`adopted-but-unavailable` 这个可选值，已填 `yes`/`no` 的项目不用改。

### 验证与范围

本地检查：模板自有测试 180 项通过、`check-development.sh` 通过（127 条登记）、
`check-shells.sh` 通过（11 个文件）、CI 在三个 PR 上通过。实测三件事：复制品跑完整套
workflow 步骤全绿（39 项 skip）；本仓库全部执行并通过；`origin` 指向模板但没有 tag 的
clone 仍按预期失败。

发布前下游风险检查（只读）：本版只改三个共享文件与一个可选 workflow 的措辞，没有 schema、
布局或 registry 字段变化；计费场景没有在真实失败的仓库上演示，提示由夹具覆盖。

### 参考

- 问题：[#198](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/198)、
  [#199](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/199)
- PR：[#200](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/200)、
  [#201](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/201)
- 前序版本：[v0.1.41](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.41)（Issue/PR 表单作为可 review 的项目文件）
- [版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.41...v0.1.42)

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
