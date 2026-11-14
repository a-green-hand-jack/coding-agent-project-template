# Release notes

本文件只描述当前发布；历史版本保留在各自的标签里（例如 `git show v0.1.37:RELEASE_NOTES.md`）。
基于本模板创建的项目维护自己的发布说明，不复制此历史。

## v0.1.39 — 2026-11-14

资产步骤改为按目录判断。没有外部载荷的派生模板可以删掉 `assets/`，诊断和 worktree 步骤
不再要求它。

- **诊断不再判红。** `diagnose-environment.sh` 在 `assets/` 不存在时打印
  `skip assets manifest` 并以 0 退出；目录存在而缺 manifest 时仍然 `FAIL`。
- **worktree 步骤不再警告。** `setup-worktree.sh` 只在目录存在时提示缺 manifest。
- **退休不再建回目录。** `migrate-assets.sh` 只在源目录存在时才在目标里创建 `assets/`。
- **没有新规则。** 保留资产的仓库行为逐字不变；本模板自身仍有 `assets/`，诊断输出相同。

### 升级时的行为

**Command only.** 三个脚本按常规替换；没有 `assets/` 的项目从现在起诊断全绿，有
`assets/` 的项目什么都不变。

### Upgrading a project from v0.1.38

1. 用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.39`。
2. 运行 `bash .agents/scripts/shared/diagnose-environment.sh`：删掉 `assets/` 的项目应看到
   `skip assets manifest`。
3. 运行 `bash .agents/scripts/shared/check-development.sh` 与本项目的检查命令。

### 验证与范围

本地检查：`check-development.sh` 通过（124 条登记）、`check-shells.sh` 通过（11 个文件）、
模板自有测试 167 项全部通过。下游验证：在 `paper-agent-project-template` v0.8.0（无
`assets/`）里运行本版 `diagnose-environment.sh`，输出 `skip assets manifest` 且无 FAIL。

### 参考

- 问题：[#185](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/185)
- PR：[#186](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/186)
- 来源：[paper-agent-project-template v0.8.0](https://github.com/a-green-hand-jack/paper-agent-project-template)
- [上一版 v0.1.38](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.38)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.38...v0.1.39)

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
