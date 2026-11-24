# Release notes

本文件只描述当前发布；历史版本保留在各自的标签里（例如 `git show v0.1.39:RELEASE_NOTES.md`）。
基于本模板创建的项目维护自己的发布说明，不复制此历史。

## v0.1.40 — 2026-11-24

升级不再把项目已经写过的内容再插一份；worktree 退休多了一个项目钩子，派发交接能写出
真实路径。三处都是下游实测到的缺口，没有新规则。

- **本地已有的块不再重复插入。** `upgrade-template.sh` 的三方合并遇到“本版新增、项目也
  手工加过”的块时会插两遍：两侧插入位置不重叠，合并报 clean，重复运行继续累加（一个
  采用项目一次运行把块从 1 份变成 2 份，`--resolved` 重试后变成 3 份）。现在合并前会去掉
  目标侧“按空行分段、本地已有逐字相同”的插入，并在计划里写明跳过了几处；同一次插入里
  既有已存在的块、也有真的新增时，只补新增。
- **worktree 退休能跑项目自己的前置检查。** `teardown-worktree.sh` 在检查与复制任何东西
  之前运行 `.agents/scripts/project/teardown-project.sh`（存在且可执行时）；非零退出即
  中止，什么都不迁移，也不打印 ready 行。没有这个文件的项目行为逐字不变。模板仍然不
  停止进程、不删除数据，停机核对仍在 `worktree-lifecycle` 第 5 步。
- **交接提示词能写出 worktree 路径。** `new-agent-prompt.sh` 增加可选 `--worktree PATH`，
  先于位置参数剥出，既有 3/4 参调用逐字不变。给了路径时提示词写明该 worktree、“不要另建
  worktree 或分支”，并把“在新 worktree 里开始”改成“在那个 worktree 里开始”。

合并行为的前后对照：

| 情形 | 本版之前 | 本版之后 |
| --- | --- | --- |
| 本版新增一段，项目已在同一文件另一处手工加了同样的内容 | 插成 2 份并报 clean，再跑再加 | 保持 1 份，计划里写明跳过了 1 处插入 |
| 同一次插入里既有项目已有的块，也有真的新增 | 两块都插 | 只补新增，已有块不重复 |
| 有 `## In this repository` 的共享文件，章节之上已有同样内容 | 判成冲突 | 报“已包含本版的改动” |

### 升级时的行为

共享脚本与文档按常规替换。新增的 `teardown-project.sh` 是可选文件：没有它就没有任何
变化；如果项目以前把守卫内联改在 `teardown-worktree.sh` 里，现在应把它移进那个钩子——
升级命令会把那处本地改动报成冲突，这正是本版要解决的情况。

### Upgrading a project from v0.1.39

1. 用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.40`。
2. 本地改过共享脚本的项目，把改动移进对应的项目文件（`teardown-project.sh`、
   `setup-project.sh`、`migrate-project.rules`），或按 `template-feedback` 报回模板。
3. 运行 `bash .agents/scripts/shared/check-development.sh` 与本项目的检查命令。

### 验证与范围

本地检查：`check-development.sh` 通过（124 条登记）、`check-shells.sh` 通过（11 个文件）、
模板自有测试 174 项全部通过，其中本版新增 5 项回归与夹具——去掉对应改动后它们会失败。
三个 PR 的 CI 检查分别通过。

真实文件复现（Issue #188 的场景，用发布前的候选脚本）：paper 派生模板 v0.4.12 的一份
本地 `Makefile`（自带 venv 块，注释和位置与模板不同）升到 v0.8.0——旧脚本把块从 1 份插成
2 份并报 clean，本版保持 1 份并报告 `already has the change of v0.8.0; 1 insertion(s)
already here`；两棵树 300 多个文件对比，唯一差异就是被去掉的那份重复块。

下游兼容性（发布前的只读 harvest）：17 条已登记采用者中 8 个落后本版（最旧 v0.1.6）；
一个采用项目内联在 `teardown-worktree.sh` 的守卫应按上面的步骤移进新钩子，另有一个采用
项目对 `upgrade-template.sh` 的本地补丁属旧实现（上游 `path_mappings` 已覆盖）。只读取
下游内容，没有执行下游测试，也没有联系任何采用者。

### 参考

- 问题：[#188](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/188)、[#190](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/190)、[#191](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/191)
- PR：[#189](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/189)、[#192](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/192)、[#193](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/193)
- 来源：[paper-agent-project-template](https://github.com/a-green-hand-jack/paper-agent-project-template)
- [上一版 v0.1.39](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.39)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.39...v0.1.40)

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
   或删掉这一块（不声明）；不用托管 CI 时删掉 `.github/workflows/template-check.yml`。
3. 运行 `bash .agents/scripts/shared/setup-worktree.sh`：它建立 `.project/`；在 `main` 上
   运行时还会幂等创建、推送 `dev`，并把 GitHub 默认分支设为 `dev`。在其它分支上或需要
   换 remote 时，手工运行 `bash .agents/scripts/shared/init-branches.sh`。工作分支从 `dev`
   开始，发布才合并到 `main`。
4. 修改 `README.md`、`USER.md` 中的项目占位内容；`DEV.md` 保留时一并改（v0.1.35 起
   下游可以删除它）。产品树不是 `src/` 时，在 `AGENTS.md` 的“三个平面”和 `README.md`
   的目录表中写明。
5. 删掉模板专用内容：registry 标 `scope: template` 的文件、本文档里的模板发布历史和这一节，
   换成项目自己的发布说明。
6. 让 coding agent 先读取 `AGENTS.md`、`.agents/AGENTS.md` 和当前 Issue，再开始修改；
   完整采用流程由 `template-adoption` 技能执行。

模板升级：`bash .agents/scripts/shared/upgrade-template.sh --check <TEMPLATE_TAG>` 输出计划，
去掉 `--check` 应用；跨过的每个版本都是 **Command only.** 且没有冲突时，一条命令加项目
检查就完成升级，否则按 `.agents/skills/shared/template-upgrade/` 走完整流程。跨项目反馈
按 `.agents/skills/shared/template-feedback/` 向模板仓库提 Issue。
