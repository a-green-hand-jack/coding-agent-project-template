# Release notes

## v0.1.35 — 2026-11-14

**继承命令按项目自己的 Python 运行、不再写字节码，registry 只记录当前状态，发布说明只描述当前版本。**

本版处理下游论文模板上报的七个继承命令/内容治理缺陷，并顺带修好它们暴露出的整包删除残留。

### 继承命令跟随项目自己的 Python

此前 `check-development.sh`、`diagnose-environment.sh`、`migrate-assets.sh`、`probe-credentials.sh` 与 `upgrade-template.sh` 只读 `${AGENTS_PYTHON:-python3}`。项目把 PyYAML 与 markdown-it-py 装进 `.project/venv` 后，`make check` 通过而直接运行这些脚本仍报依赖缺失。现在五个命令统一按 `AGENTS_PYTHON` → 存在且可执行的 `.project/venv/bin/python3` → `PATH` 上的 `python3` 选择解释器（#162、PR #169）。

### 继承入口不写字节码

四个启动 Python 的命令在启动前 `export PYTHONDONTWRITEBYTECODE=1`，`content_registry.py` 入口设 `sys.dont_write_bytecode = True`，CI 与文档的测试发现命令也带上该变量。此前只有 `-B` 覆盖经 `make` 启动的进程，直接调用测试发现仍会把 `__pycache__` 写进源码树；这些缓存被 Git 忽略，不会被发现也不会被清理，只会在 teardown 时表现为多出来的 ignored state（#166、PR #169）。

### 迁移规则明确 `tools/` 与 `venv/` 属于项目

`migrate-assets.sh` 与 `DEV.md` 写清 `.project/tools/<tool>/`、`.project/venv/` 是项目条目，由项目的 `migrate-project.rules` 声明（`tools|drop|WHY`、`venv|drop|WHY`），模板不替它决定保留与否；`no rule for it` 提示补了例子，并有回归测试锁定（#163、PR #170）。

### 继承脚本与共享指引不再依赖根目录 `DEV.md`

跟随模板的项目可以删除根 `DEV.md`。诊断的补录提示改为读取 registry 的 `template:` 块与发布 tag（`git tag --sort=-v:refname`、adoption commit），本地验收统一指向 `issue-workflow` 的 `<LOCAL_CHECK>` 槽位；`template-upgrade`、`issue-workflow`、`template-adoption` 的相应措辞一并去掉文件名假设（#164、PR #171）。

### 可选技能只在采纳时被引用

`long-running-supervision` 是 `optional: true`，项目可以登记为 `rejected`。迁移提示只在目录存在时提到它，`issue-workflow` 的正文改为“若本仓库采纳了这个可选技能”（#165、PR #172）。

### 发布说明只描述当前版本

`RELEASE_NOTES.md` 不再累积历史：HEAD 只保留当前版本条目，历史留在各 release tag 里。`upgrade-template.sh` 从目标版本开始，逐个用 `git show <tag>:RELEASE_NOTES.md` 读取被跨过版本的条目，并按条目里的 `### Upgrading a project from <上一个 tag>` 找到下一个 tag；缓存里只有两端时按需 fetch。读不到某个被跨过版本、条目缺失或未命名前一个 tag 时，列为 manual 项并停止回溯，不再默认完成（#168、PR #175）。

### registry 只记录当前状态

registry 顶层的 `legacy_inventory`、`local_legacy_inventory` 与 `migrations` 已删除（4962 → 1572 行），历史在 Git 与各 release tag 里。检查器遇到这三个块会给出一条明确错误；升级命令删除本地残留的三个块并在计划里报告。`minimum_upgrade_source: v0.1.34` 声明升级下限，更老的来源以退出码 2 拒绝并提示逐版本升级或重新采用（#167、PR #176）。

删除语义随之对齐：`D` 删除不再经迁移表别名重映射到新布局，而是落在真实路径；删除后按文件实际存在情况移除不再覆盖任何文件的登记条目。此前“整包删除后旧布局残留、其中的相对链接指向已删除文件”的问题（#174）因此消失，并新增“整包删除无残留、重复升级幂等”的回归测试。

### Upgrading a project from v0.1.34

**Command only.**

用目标版本完整的命令目录（`upgrade-template.sh` 与 `content_registry.py`）执行 `bash .agents/scripts/shared/upgrade-template.sh v0.1.35`：共享文件按常规规则替换，本地 `## In this repository` 段保留；registry 里残留的 `legacy_inventory`、`local_legacy_inventory`、`migrations` 被删除并在计划中报告；`template.version` 更新为 v0.1.35。之后运行项目自己的本地检查。

本版移除了迁移表的路径回放：今后上游移动内容时，升级不再自动搬移项目侧文件，移动步骤会写进对应版本的 `### Upgrading a project from …` 段。低于 `v0.1.34` 的来源不再机械升级，先用 v0.1.34 的命令升到 v0.1.34，或按 `template-adoption` 重新采用。

### 验证与范围

本地门禁：`check-development.sh`、`check-shells.sh`、`diagnose-environment.sh` 通过，模板自有测试（159 → 166 项）全部通过。真实 release 套件从 v0.1.34 升级到本版，与“从本版新建的项目”逐文件比较一致；重复升级字节不变。本模板没有产品运行时，因此本版没有真实运行、构建或发布面之外的验证。

### 参考

- 问题：[#162](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/162)、[#163](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/163)、[#164](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/164)、[#165](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/165)、[#166](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/166)、[#167](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/167)、[#168](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/168)、[#174](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/174)
- PR：[#169](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/169)（#162、#166）、[#170](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/170)、[#171](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/171)、[#172](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/172)、[#175](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/175)、[#176](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/176)（含 #174）
- 来源：[paper-agent-project-template#221](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/221)、[#222](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/222)、[#223](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/223)、[#226](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/226)、[#229](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/229)、[#230](https://github.com/a-green-hand-jack/paper-agent-project-template/issues/230)
- [上一版 v0.1.34](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/v0.1.34)；[版本比较](https://github.com/a-green-hand-jack/coding-agent-project-template/compare/v0.1.34...v0.1.35)
