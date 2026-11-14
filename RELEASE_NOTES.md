# Release notes

本文件只描述当前发布；历史版本保留在各自的标签里（例如 `git show v0.1.37:RELEASE_NOTES.md`）。
基于本模板创建的项目维护自己的发布说明，不复制此历史。

## v0.1.38 — 2026-11-14

README 只写给产品。模板自己的起步手续、版本选择和升级细则不再占据 human 入口。

- **README 分成两层。** 标题与三个平面、快速开始、这个项目怎么跑、目录、边界、分支
  模型与可见性、论文项目、发布；每个主题只留决定和命令，细则指向权威处。
- **起步手续换位置。** “Use this template / 克隆 release tag → setup → 填占位内容 →
  删模板专用内容 → 让 agent 读 `AGENTS.md`”搬进本文件末尾的
  `## Starting from this template`，README 只留指针；`USER.md` 的选择模板版本也指向
  这一节，不再有悬空引用。
- **补上“这个项目怎么跑”。** 产品树 `src/`、`pyproject.toml`/`Dockerfile`/`install.sh`
  三个可选骨架怎么换成真的、验证与检查命令，以及输出为什么落在 `.project/`。
- **前置条件写在命令旁。** GitHub CLI、已配置的 `origin`、`python3` 加 PyYAML 与
  markdown-it-py（或 `AGENTS_PYTHON`）和命令写在一起；`init-branches.sh` 与 `DEV.md`
  的分支模型对齐：在 `main` 上首次 setup 已幂等创建 `dev`，只有需要改分支名或补推时才
  手工运行。
- **目录表补齐。** 增加 `AGENTS.md`、`.github/`、`.env.example`、`RELEASE_NOTES.md`、
  `RELEASE_EXAMPLE.md`、`DEVELOPMENT_WRITING_EXAMPLE.md` 和 `.gitignore`。
- **`credentials.yaml` 不再凭空声称。** 本模板不调用 LLM，说法统一为“采用后由
  `llm-credentials` 建立”；`AGENTS.md`、`DEV.md`、`.env.example` 同步。
- **registry 与正文一致。** `README.md` 改为 `shared_with_adaptation` + `upgrade: review`：
  升级命令不再假装它由模板拥有，也不改写已采用项目的 README，只打印本版差异供审阅。

### 升级时的行为

`README.md` 登记为 `upgrade: review`，升级命令不会改动已采用项目的 README，只在计划里
打印本版差异并归入 “Review (left to the project)”；改写与否由项目自己决定。

### Upgrading a project from v0.1.37

**Command only.**

用本版完整的命令目录执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.38`。
共享文件按常规规则替换，本地 `## In this repository` 段保留。`README.md` 是
`upgrade: review` 文件，命令不改写它：需要新形状时按本版的 README 自行重写，不重写也
不影响升级。

### 验证与范围

本地检查：`check-development.sh`（含索引一致）、`check-shells.sh` 通过，模板自有测试
167 项全部通过。本模板没有产品运行时，因此本版没有真实运行或构建面之外的验证。

### 参考

- 问题：[#182](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/182)
- PR：[#183](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/183)
- 来源：[paper-agent-project-template v0.7.0](https://github.com/a-green-hand-jack/paper-agent-project-template/releases/tag/v0.7.0)
- [上一版 v0.1.37](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.37)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.37...v0.1.38)

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
