# Release notes

## Unreleased

收进下游在 v0.1.13 上的反馈（#70，合并了 #65–#69）。

- **CI**：`.github/workflows/template-check.yml` 只在指向 `dev`、`main` 的 PR 和推送到 `dev`、`main` 时运行，加了 `concurrency`（同一 ref 的新运行取消旧运行）和 10 分钟超时；模板自己的测试步骤只在存在 `.agents/tests/test_template_*.py` 时运行，下游跳过。registry 把它登记为 `shared_with_adaptation`、`optional: true`：`template-adoption` 按 `issue-workflow` 的 `<CI>` 采用或拒收，`template-upgrade` 保持拒收。
- registry 新增条目字段 `optional: true`（项目可以不采用，升级保持不采用）和 `upgrade: review`（项目开始后归项目所有，升级只打印 diff 供审阅），在 `entry_fields:` 说明。标为可选的还有产品骨架（`pyproject.toml`、`Dockerfile`、`install.sh`、`.dockerignore`）、`llm-credentials`、`third-party-llm-compat-patches`、`docker-objects-prefixed-and-removed` 和 `gpt5-strict-backend-requests`，这些本来就是按需采用的内容。
- **采用期诊断**：本地和 `origin` 都没有 `dev`、当前分支不是 `main` 时，`diagnose-environment.sh` 把三行分支检查（本地 `dev`、`origin/dev`、GitHub 默认分支）报为 `warn` 并保留 `init-branches.sh` 提示；`dev` 一旦存在，`origin/dev` 或默认分支不对仍是 `FAIL`。`template-adoption` 第 6 步写明合并前这些 warning 是预期的。
- **升级命令** `bash .agents/scripts/upgrade-template.sh [--check] [--resolved PATH]... <TARGET_TAG>`：
  - 从 registry 读所跟随的模板（`template.upstream` 优先），把两个 tag 取到 `.project/state/template-upgrade/` 下的可复用克隆，之后可离线运行；
  - 对两个 tag 间每个变更路径按目标版本 registry 执行 `template-upgrade` 第 5 步（被删路径按源版本）：
    - 跳过 `scope: template` 和项目自有路径，可选内容未采用时保持不采用；
    - 共享文件在检查 1 后替换 `## In this repository` 段以上的文本，没有该段时整体替换，本地改过则三方合并；新增路径加入，被删路径只在本地未改时删除；
    - 从不碰 `assets/`、`.project/` 和 `.env`；
  - 逐键、逐条合并 registry：`template` 块保留本项目的 repository 和 version，`writing:` 块从不改动，没有冲突时才把跟随的版本改为目标；
  - 本地修改与发布的修改重叠时一律视为冲突，不覆盖，并在 `proposals/` 下给出 `git merge-file` 三方合并建议，命令非零退出；槽位或所关联步骤变了的段列为手动步骤；
  - 打印应用、跳过、拒绝、审阅、手动各项，跨过的每个版本的升级段，以及 `Light path: yes|no`；`--check` 只打印计划，不改项目文件。
- **轻量路径**：模板每个版本的 release notes 都有 `### Upgrading a project from <上一个 tag>` 段，以 `**Command only.**` 开头或列出手动步骤，`release-doc-audit` 检查这一点。跨过的版本都是 command only 且 `--check` 没有冲突和手动项时，升级就是一个 Issue、命令、项目检查和 PR，不画迁移图，按 mechanical 档派出；否则走完整流程，以命令的计划为迁移地图的起点。还没有这条命令的仓库用 `template-upgrade` 里的 bootstrap 命令运行目标版本中的副本。
- **凭据清单**（叠加在 `llm-credentials` 上，共享凭据文件不变）：
  - 设备级 `inventory.yaml` 放在共享文件旁（0600），每个变量一行，只记名字和事实（service、kind、purpose、endpoint、auth、scope、status、owner、verified、notes、probe），空占位必须标为 `empty-placeholder`；
  - 项目级、受跟踪的 `credentials.yaml` 写明需要哪些行、工具用什么名字读取、给哪个沙箱或岗位、必需还是可选，以及在 `CREDENTIAL_DIR/overrides.env` 里的本机覆盖；
  - 新脚本 `probe-credentials.sh`：`--check` 不联网，检查清单完整性和项目需要的行；不带参数时运行只读的 `GET` 探测，只输出 `credential <name>: ok | failed | not-probed`；值只在进程内读取，不进入命令行、输出或文件；
  - `setup-worktree.sh` 对缺行、空占位和未设置的必需凭据报错并以非零退出；`diagnose-environment.sh` 给出每个凭据的状态，必需凭据失败时 `FAIL`；没有 `credentials.yaml` 或设备上没有共享文件时只给 `skip`；
  - 端点和权限范围以清单行为准，知识记录引用清单行而不重复；`.env.example` 关于 `*_FILE` 的说明与 `llm-credentials` 一致，指向项目内的链接。
- **写作约定**：registry 的 `writing:` 块声明工作语言（Issue、PR、评论、交接 prompt 中 Issue 专属部分、human 文档）和 Issue 开头段落；模板共享文本保持模板语言，不翻译。放在 registry 是因为模板和每个项目都有它，模板仓库自己不能在共享 skill 里写段；放在 `AGENTS.md` 会被升级合并进没有声明的下游。`template-adoption` 映射它，`template-upgrade` 从不改它，`new-agent-prompt.sh` 把它写进交接 prompt，未声明的项目行为不变。本仓库声明：Issue、PR、human 文档用中文。
- **分阶段工作**：`issue-workflow` 新增 “Phased work”：一个父 Issue 加每阶段一个子 Issue（GitHub sub-issue 关系，父 Issue 列清单），每个阶段照常走 Issue 流程；给出 `gh api graphql` 的 `addSubIssue` 用法（请求头 `GraphQL-Features: sub_issues`）。
- 模板自己的测试 `.agents/tests/test_template_*.py`（`scope: template`）：升级命令的夹具仓库测试和从较旧真实版本到候选版本的升级测试、凭据测试、采用期分支检查测试；CI 运行它们。

### Upgrading a project from v0.1.13

v0.1.13 还没有升级命令：先按 `template-upgrade` 的 bootstrap 命令运行本版本中的 `upgrade-template.sh`，它完成机械部分。然后：

1. `issue-workflow` 的 `<CI>` 为 `no` 而项目仍有 `.github/workflows/template-check.yml` 时，删掉它（拒收）；以后的升级保持它不存在。
2. 派生模板若在 `template-adoption` 的 `## In this repository` 段里把采用期的三行分支检查写成预期失败，删掉这条说明。
3. 决定是否在 registry 写 `writing:`（工作语言和 Issue 开头段落）；不写则行为不变。
4. 调用 LLM 的项目决定是否采用凭据清单：在设备共享文件旁建 `inventory.yaml`，在项目根目录写 `credentials.yaml`（可以从 `.env.example` 的变量名起草），再运行 `bash .agents/scripts/probe-credentials.sh --check`。`.env.example` 是项目自己的文件，命令不改它；需要时按 `llm-credentials` 改写其中关于 `*_FILE` 的说明。

## v0.1.13 — 2026-10-20

- Declared product tree: a project declares its product tree in `AGENTS.md` and the `README.md` directory table, with `src/` as the default. A non-code product tree, such as a paper's `paper/`, follows the same rules: it is self-contained, never reads `.agents/`, and builds into `.project/`. `AGENTS.md`, `README.md`, `DEV.md`, the registry notes, `template-adoption` and `template-upgrade` say so.
- New registry field `template.upstream` (`repository`, `version`) for a derived template, a template built from this one that projects are made from: its `template` block names itself and its own release, and `template.upstream` names the template it follows and that template's tag. A project made from a derived template records only that template and removes the copied `upstream` block. `DEV.md` ("与模板的关系") defines the field with a table of the four repository kinds, and the registry carries it as a comment.
  - `template-adoption` writes it when the target is a derived template and never copies it from a derived template into a project; a project made from a derived template continues the derived template's `## In this repository` sections.
  - `template-upgrade` reads the followed template from `template.upstream` when present and moves `template.upstream.version` to the target tag, leaving the derived template's own `template.version` alone; the section reconcile step also carries over a derived template's section changes.
  - `template-feedback` routes a defect in content a derived template inherited to `template.upstream.repository`; a project made from a derived template reports to that template, which forwards inherited defects upstream and links the Issues.
  - `release-doc-audit` prints the whole `template` block and accepts the recorded upstream tag as a version reference.
  - `diagnose-environment.sh` reports the upstream template, fails when `template.upstream` lacks `repository` or `version`, and warns when a repository whose origin is not `template.repository` carries an `upstream` block.
- `template-harvest` recognizes a derived template by `template.upstream` and pins it to `template.upstream.version`, skips projects made from another template, and lists the public paper template [`paper-agent-project-template`](https://github.com/a-green-hand-jack/paper-agent-project-template) as a known derived template. `README.md` names it as the starting point for papers.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.12 — 2026-10-19

- Added the `resolve-real-paths-before-moving` shared memory record: before moving, copy-then-deleting, replacing or symlinking a directory, resolve both paths (`readlink -f`, device and inode) and stop on overlap; verify two different data sets; confirm the delete frees space; let a person choose which copy to delete. Linked from `asset-lifecycle`.
- `llm-credentials` rule 4: a credential never travels as a command-line argument (readable through `ps`); pass it as an environment variable selected by name (`docker run --env KEY`) or through the tool's own channel (`GIT_CONFIG_*` for git headers).
- 工作单元分级：较大的改动仍走 Issue → worktree → PR；文档、注释、memory/索引、拼写、
  单文件且没有设计决定的小修复，以及不改产品代码的验收运行，可以直接在 `dev` checkout
  里做。拿不准时按大的走；小改动变大或出现设计问题时停下来开 Issue。`AGENTS.md`、
  `DEV.md` 和 `README.md` 同步说明，`issue-workflow` 增加 "When this flow is not needed" 一节。
- `template-harvest` works through GitHub only: adopters are found with `gh repo list` and read with `gh api` (registry marker, tree comparison against a release tag, comparison from the watermark), the local state is keyed by repository, and requests to an adopter are Issues. The local-roots and worktree-resolution steps are gone; a note covers converting an older local-path record.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.11 — 2026-10-18

- `migrate-assets.sh` reads an optional, project-owned `.agents/scripts/migrate-project.rules` (one `NAME|ACTION|WHY` line per `.project/` entry the project's setup hook creates; actions `copy`, `drop` with a reason, `login`), so a downstream's own entries no longer stop every teardown and a local edit to the script is not needed. `login` is the rule the script already applied to `credentials`: a link to the canonical checkout's login is dropped, a real copy blocks, and `--also`/`--skip` on a login is refused (exit 2). A rule for an entry the template handles itself is refused, so a new template rule shows up as a conflict after an upgrade. `template-adoption` step 5, `template-upgrade` step 5, `llm-credentials`, `issue-workflow` and `DEV.md` describe it.
- Added the `docker-objects-prefixed-and-removed` shared memory record (`shared_with_adaptation`, parameter `DOCKER_PREFIX`): everything a project starts in Docker carries its prefix, what expires is removed promptly and only the project's own and never with `-f`, and `issue-close-out` removes the image tags only the merged branch used.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.10 — 2026-10-16

- `release-doc-audit`: the example `RELEASE_HEADING` for notes that title only the current release now ends the tag like the default (`([[:space:]]|\$)`), so a shorter tag such as `v0.4` no longer matches a `v0.4.0` title.
- `template-adoption` step 5: a slot value that does not fit a Slot/Value table cell (a pattern or command containing `|`) is written as a code block under the `## In this repository` section, naming its slot.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.9 — 2026-10-15

- Shared skills and memory records registered `shared_with_adaptation` keep the template text verbatim; each adopter writes its slot values and step-keyed additions in one trailing `## In this repository` section, so `template-upgrade` replaces the text above it without conflicts. `template-adoption`, `template-upgrade`, the registry rule and `issue-workflow` state the convention, and `diagnose-environment.sh` warns when a downstream file lacks the section.
- `issue-workflow` checks the dev checkout for a live run before every pull or merge, and close-out stops on any container (running or stopped) that mounts the worktree: `inspect-state.sh` lists them and exits 3. `long-running-supervision` forbids editing code under a live run in place.
- `issue-workflow` Start labels the Issue workspace `<WORKSPACE_PREFIX>-issue-<N>`.
- `diagnose-environment.sh` fails, with the fix, when `.env.example` or `assets/MANIFEST.yaml` is ignored by Git or `.project/` is not; `template-adoption` names the `.gitignore` entries to merge.
- `template-feedback` asks for the kind of downstream instead of naming a private repository.
- `release-doc-audit` is `shared_with_adaptation`, with a `RELEASE_HEADING` parameter for the release-notes layout.
- Added the shared `product-state-root` memory record (state root from the setup marker), the shared `third-party-llm-compat-patches` memory record and the first shared knowledge record, `gpt5-strict-backend-requests`, linked from `llm-credentials` and `template-adoption`.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.8 — 2026-10-15

- Added the shared `llm-credentials` memory record: stable keys in one device-level shared file reached through a project-local link, refreshing logins once per project in the canonical checkout's `.project/credentials`, only selected variables passed to children, and safe re-login (never through a link, keep the failed login, the maintainer logs in). `setup-worktree.sh` links a worktree's `.project/credentials` to the canonical checkout; `migrate-assets.sh` drops that link and blocks on a real login copy.
- Added dispatch by difficulty to `issue-workflow`: four tiers with explicit model and effort slots, a Dispatch section in the Issue body, and a fallback agent only when the primary is unavailable; recorded in the shared `issue-dispatch-by-difficulty` memory.
- Issue handoffs now carry four working rules (`new-agent-prompt.sh`, `issue-workflow`): verify to completion and report one definite result, fix related defects met on the way, leave conflicts between worktrees to the dev checkout, and merge approval covers the close-out. `DEV.md` and the PR template no longer ask for a "not verified" list.
- Added the shared `run-settings-from-config` memory record: run parameters are settings with a fixed override order, recorded at run start and reused on resume.
- Removed the empty top-level `tests/` directory and its references.
- Recorded the 2026-10-15 downstream harvest in project memory.

## v0.1.7 — 2026-10-13

- Added the shared `issue-workflow` skill covering Herdr start, merge and close-out, with adaptation slots for agent, repository, CI and product commands.
- Added shared memory records for implementing each Issue in its own Herdr worktree and closing it out after merge, and populated the shared memory index.
- Added a "Backfill a missing template record" step to `template-upgrade` and `template-adoption`, and made `diagnose-environment.sh` explain how to backfill a missing registry `template` block instead of failing without a reason.
- Added the maintainer-only `template-harvest` skill (`scope: template`) and wired it into the release checklist: it discovers adopters from the registry marker, inventories what they settled, and brings reusable practice back through the normal Issue process.
- `setup-worktree.sh` now gives a new worktree the primary checkout's asset-link mappings and hand-made `assets/` links, with the worktree's own mapping first; `diagnose-environment.sh` checks both link files.
- `migrate-assets.sh` now names every `.project/` entry with its action, size and reason; stops on an unknown entry that holds something until `--also`/`--skip` decides it; merges asset-link mappings into the destination; and verifies the copy afterwards, writing a `migration-report.txt`. `teardown-worktree.sh` passes `--also`/`--skip` through.
- `DEV.md` documents the template relationship: which tag a project follows, upgrade through `template-upgrade`, feedback through `template-feedback`, and its own release notes.
- Release documentation audit fixes: `README.md` and `USER.md` no longer pin a stale example tag (they use a `<TEMPLATE_TAG>` placeholder), and `release-doc-audit` names the release being prepared in its `TARGET_TAG` example.

## v0.1.6 — 2026-10-08

- Fixed release-doc-audit version scanning to include hidden development-plane files.

## v0.1.5 — 2026-10-08

- Added the shared `release-doc-audit` skill for pre-release documentation checks.
- Recorded the adopted template repository and version in the content registry.
- Classified template release notes and separated them from downstream release history.

## v0.1.4 — 2026-10-07

- Added optional package, container and installer skeletons for product releases.
- Added `.dockerignore` boundaries and diagnostics to keep development files out of products.
- Documented adoption and upgrade handling for existing build and install contracts.

## v0.1.3 — 2026-10-07

- Structured memory and knowledge into shared/project topic directories.
- Added front matter templates and rules-only indexes.
- Updated governance, adoption and upgrade guidance for legacy single-file records.

## v0.1.2 — 2026-10-07

- Added idempotent `dev`/`main` branch initialization and diagnostics.
- Documented Herdr worktree and new-pane agent handoff for Issue work.
- Kept machine-specific asset links out of Git and fixed tracked-asset migration.
- Added repository visibility guidance and checks for public writes and template feedback.

## v0.1.1 — 2026-10-06

- Added `template-adoption` for migrating existing repositories into the template.
- Added `template-upgrade` for controlled downstream upgrades between releases.
- Added copy-ready user prompts for both operations.

## v0.1.0 — 2026-10-06

- Initial three-plane coding-agent project skeleton.
- Visible worktree state, setup, diagnostics, asset migration and teardown.
- Claude Code discovery through `CLAUDE.md -> AGENTS.md`.
- Shared skills for worktrees, memory governance, assets, CLI operations,
  long-running supervision and downstream template feedback.
- GitHub Issue/PR templates and template structure checks.
