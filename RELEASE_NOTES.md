# Release notes

## Unreleased

- **Issue session 的工作文件不再让 close-out 停下**（#92）：`new-agent-prompt.sh` 的交接规则和 `issue-workflow` 的 “Issue session rules” 新增一条：session 自己的工作文件（计划、PR 正文草稿、给协调者的消息）放在 `.project/state/`，不放 `.project/` 根目录；`state/` 本来就总是被复制。`migrate-project.rules` 的 `NAME` 现在可以是 shell 通配符（`*`、`?`、`[...]`），一行管一类文件，例如 `plan-*.md|copy|`。`migrate-assets.sh` 的匹配顺序：模板规则、项目的精确名字、项目的通配符（按文件里的先后，第一个匹配的生效）；报告的 WHY 列写出匹配到的规则（`rule plan-*.md`）。校验不过以 exit 2 退出并指出行号：通配符不能含 `/`，不能是 `login`，不能匹配模板自己处理的条目名（`state`、`runs`、`artifacts`、`manifest`、`assets.links`、`home`、`worktree.env`、`credentials`，所以 `st*` 或 `*` 会被拒绝）；`drop` 仍须写理由。没有规则对应的根目录文件仍然 exit 3，`--also`、`--skip` 照旧按单个文件名覆盖。`issue-workflow`、`template-adoption`、`DEV.md` 同步说明。新增回归测试 `.agents/tests/test_template_migrate.py`。
  - 兼容：`NAME` 里含 `*`、`?`、`[` 的规则以前只匹配这个字面名字，现在按通配符匹配。这种规则不太可能存在；如果有，检查它是否仍然只匹配想要的文件，或者匹配到模板条目而被拒绝。`template-upgrade` 照旧保留项目的 `migrate-project.rules`。
- **Issue 之间的依赖记在 GitHub 的 blocked-by 上**（#93）：`issue-workflow` 不再靠正文文字或协调者的记忆记“谁等谁”，按依赖决定并行还是等待，不新增脚本、状态文件或标签。
  - “Phased work” 第 3 步新增依赖表：并行（只挂父 Issue，同时派）、串行（`gh issue edit <B> --add-blocked-by <A>`，A 合并并 close-out 后从新的 `dev` 派 B）、同步（必须一起落地就不拆，一个 sub-issue、一个 PR）、异步（先把接口写定，写进父 Issue 或做成小的接口 sub-issue，A、B 都 blocked-by 它，之后并行）。每个 sub-issue 都从最新的 `dev` 开工，不叠在未合并的分支上。原第 3 步改为第 4 步（认领父 Issue 的协调者按依赖派出）；原第 4 步改为第 5 步，用 `gh issue create --parent` / `gh issue edit --parent` / `--add-sub-issue` 取代 GraphQL `addSubIssue`，blocked-by 的写法和读法写在旁边。
  - Start 第 1 步新增前提：用 `gh issue view <N> --json blockedBy` 确认没有还开着的 blocker，有就不派并报告在等哪个 Issue。Close-out 新增第 10 步：用 `--json blocking` 列出这个 Issue 阻塞过的 Issue，自己认领且已无开着 blocker 的按 Start 派出，别人认领的不动。
  - “Several coordinators” 补充跨协调者的依赖：用 blocked-by 记下并等它合并，不进它的 worktree、不催它的 session，要催找维护者。“Independent Issues run in parallel” 的“只有真实依赖才等”改为指向 blocked-by。
  - 共享 memory `speed-and-parallelism-by-measurement`、`issue-in-herdr-worktree` 各补一句：依赖记在 blocked-by 上。
- **合并只看本地检查，CI 只在 PR 上标记**（#98）：GitHub Actions 因计费跑不起来时，job 一步没执行就被标成 failure，PR 永远不会变绿，协调者只能停下。现在 `issue-workflow` 里没有任何一步以 CI 的结果作为合并或继续的条件，不新增脚本或状态文件。
  - 槽位：`<POST_MERGE_CHECK>` 改名为 `<LOCAL_CHECK>`，不论 `<CI>` 是什么都要填，内容是 `DEV.md` 的检查命令，和 CI workflow 跑的步骤一致。`<CI>` 只表示是否采用可选的 `.github/workflows/template-check.yml`。本仓库的值写在 `issue-workflow` 新增的 `## In this repository` 段，和 `template-check.yml` 的步骤一一对应。
  - Merge 第 2 步：去掉以 `gh pr checks` 为合并门槛的要求。协调者在这个 PR 的 worktree 里、PR 最新的提交上跑 `<LOCAL_CHECK>`（`<PRE_MERGE_GATE>` 照旧在第 3 步），在 PR 上留一条评论：commit SHA、每条命令和结果、CI 状态（通过 / 失败 / 没运行，用 `gh pr checks` 读一次，不等）。`<LOCAL_CHECK>` 全部通过并有维护者批准即可合并，没通过就不合并，交 Issue session 修；CI 失败而本地通过时只在评论和报告里写明“CI 和本地结果不一致”，不挡合并，由维护者决定要不要开 Issue 查。第 4 步（解决冲突后）和第 5 步（合并后在 dev checkout `git pull --ff-only`）一律跑 `<LOCAL_CHECK>`；merge commit 上的 CI 只记在报告里。发布 PR（`dev` → `main`）同样按本地检查合并。
  - Issue session 规则（`issue-workflow` 和 `new-agent-prompt.sh`）：session 跑本地检查并报告；推送后可以读 `gh pr checks` 并报告状态，但不等它，也不因为它没运行而停下。
  - `template-adoption`、`content-registry.yaml` 里 `template-check.yml` 的 note、`DEV.md` 和 `template-check.yml` 的头注释同步说明；`template-check.yml` 跑的内容不变。

### Upgrading a project from v0.1.17

1. 运行 `upgrade-template.sh`。它替换 `migrate-assets.sh`、`new-agent-prompt.sh`，以及 `issue-workflow`、`template-adoption`、`speed-and-parallelism-by-measurement`、`issue-in-herdr-worktree` 在 `## In this repository` 段以上的文本；各项目的 `## In this repository` 段和 `migrate-project.rules` 保持不变。
2. 如果 `migrate-project.rules` 里有 `NAME` 含 `*`、`?`、`[` 的行，按上面 #92 的兼容说明检查一次。
3. `issue-workflow` 的 `## In this repository` 段如果有按 “Phased work” 第 3 步（原：互不依赖的同时派）或第 4 步（原：GraphQL `addSubIssue`）写的补充，改挂到新的第 4 步和第 5 步；Close-out 的补充在第 10 步之前不受影响。已有的 sub-issue 之间如果靠正文文字记了先后，用 `gh issue edit <B> --add-blocked-by <A>` 补记，并删去那句文字。
4. （#98）把 `issue-workflow` 的 `## In this repository` 段里的 `<POST_MERGE_CHECK>` 改名为 `<LOCAL_CHECK>`。原来 `<CI>` 为 `yes`、没填这一项的项目要补上：填 `DEV.md` 的检查命令，和自己的 CI workflow 跑的步骤一致；`<CI>` 为 `no` 的项目只改名。该段里如果写过以 `gh pr checks` 为合并门槛的要求或要求 CI 先通过，改成按 `<LOCAL_CHECK>` 合并、CI 只标记。`upgrade-template.sh` 同时替换 `new-agent-prompt.sh`、`template-adoption` 在 `## In this repository` 段以上的文本。

## v0.1.17 — 2026-10-24

收进下游反馈 #85，整理 `.agents/memory`（#87），并支持 dev checkout 里多个协调者并行（#89）。这一版有手动步骤，见升级段。

- **充分利用现有 coding agent**（#85）：新增共享 memory `serve-the-coding-agent`，登记为 `shared_with_adaptation`、`optional: true`。我们不自己从头造 agent：指导、工具、并行、轨迹、成本这五根支柱是给它搭的干活条件，它已经会做的事不重写、它的判断不代替；每项改动至少帮到一根，哪根都不帮的代码是删除候选，撑着某一根的东西不为省代码而删。记录写明：评审改动时问一句这次帮的是哪一根；改了检查规则就在同一个改动里改说明，改了验收标准要确保有检查或审核能判断；运行中逐次请求记账（未命中缓存的输入、命中缓存的输入、输出），花费从运行记录读而不是写报告时拼凑；轨迹和花费只整理一次，审核读命令整理出的固定格式摘要；加共享文件、全局锁或全局缓存前先确认它不会让本来能并行的运行变成排队。并行部分只链接 `speed-and-parallelism-by-measurement`，不重复其规则。

- **memory 只放决定和理由**（#87）：步骤搬进 skill，会变的格式和脚本行为搬进 knowledge，规则的意思不变、也没有新增规则。
  - `llm-credentials` 只留六条决定、理由和两个参数 `SHARED_CREDENTIAL_FILE`、`CREDENTIAL_DIR`（文件名和参数不变）。原 Apply 第 1–5 步、“探测确定事实后记进清单行”和 worktree 链接登录目录、teardown 不复制登录的规则搬进新的共享 skill `credential-setup`；`inventory.yaml`、`credentials.yaml` 的格式和 `probe-credentials.sh` 的检查与输出搬进新的共享 knowledge `credential-inventory`。两项都登记为 `optional: true`，跟 `llm-credentials` 一起采用或不采用；`template-adoption` 第 3 步把它们和 `llm-credentials` 一起映射。
  - `resolve-real-paths-before-moving` 只留决定和那次丢数据的经过；六步检查、命令、要报告的证据以及脚本和 teardown 怎样遵守，搬进 `asset-lifecycle` 新的一节 “Before moving, replacing or deleting a directory”。
  - `issue-in-herdr-worktree`、`issue-close-out`、`issue-dispatch-by-difficulty` 去掉复述 `issue-workflow` 的步骤，指向 Start、Dispatch by difficulty、Merge、Close-out。`issue-close-out` 里“合并的 PR 改了镜像或测试 fixture 时删掉只有该分支用的镜像 tag”补进 `issue-workflow` Close-out 第 8 步。
  - 维护者侧：`template-harvest` 每次运行不再写一条 memory，细节只在运行报告、发布说明和 `adopters.yaml`；长期决定（被否掉的候选和原因）合进项目 memory `harvest-decisions`，原来 10 条 `harvest-*` 记录删除。交付副本（带模板标记、但是另一个下游的副本）不单独算一个下游，写进 skill 第 1 步。

- **dev checkout 里可以有多个协调者**（#89）：`issue-workflow` 不再假设 dev checkout 里只有一个协调 session。
  - 新增 “Several coordinators”：每个协调者认领一个 Issue（连同它的 sub-issue），只动自己认领的 Issue 的 worktree、session、PR 和分支；别人认领的 Issue 不碰，接手由维护者决定。认领时协调者先用 `herdr agent rename "$HERDR_PANE_ID" <AGENT_PREFIX>-coord-<N>` 给自己一个能在 Herdr 里找到的名字，确认 Dispatch 段没有别人的 `- coordinator:` 行后写上自己，再读一遍确认。查看别人在干什么只用现有命令：`gh issue list`/`gh issue view`/`gh pr list` 看认领和进度，`herdr agent list`、`herdr worktree list` 看正在跑的 session 和 worktree。没有新脚本、状态文件或锁。
  - Merge：PR 和当时的 `dev` 冲突时，认领的协调者在**这个 PR 自己的 worktree** 里把最新的 `dev` 合进分支、解决、经维护者确认后推送，再在 GitHub 上合并；可以自己做（Issue session 空闲时），也可以交给 Issue session。共用的 dev checkout 只做 `git pull --ff-only`。机械冲突两边保留，语义冲突交维护者。合并后的 CI 按本 PR 的 merge commit 查，不看最近一次运行（可能是别的协调者的）；`<CI>` 为 `no` 时先 pull 再在 dev checkout 跑 `<POST_MERGE_CHECK>`。
  - Shared boundaries 新增共用 dev checkout 的规矩：不留下做了一半的状态；小改动只 `git add` 自己的文件、提交后马上推送，推送被拒就报告；`pull --ff-only` 因为别人的本地改动或提交失败时报告并等待，不 stash、不 reset、不替别人提交。
  - “Phased work” 新增第 3 步：认领父 Issue 的协调者派出每个 sub-issue 的 worktree，互不依赖的同时派，有依赖的等前一个合并（原第 3 步顺延为第 4 步）。
  - `issue-close-out`、`issue-in-herdr-worktree` 和 `new-agent-prompt.sh` 的交接规则同步改为：冲突由认领的协调者在合并时、在本 worktree 里处理。

### Upgrading a project from v0.1.16

1. 运行 `upgrade-template.sh`。它替换 `llm-credentials`、`resolve-real-paths-before-moving`、三条 `issue-*` 记录以及 `asset-lifecycle`、`issue-workflow`、`template-adoption` 在 `## In this repository` 段以上的文本，并合并 registry；各项目的 `## In this repository` 段保持不变。
2. 命令把三项新的可选内容列为手动项：`serve-the-coding-agent`（共享 memory）、`credential-setup`（共享 skill）和 `credential-inventory`（共享 knowledge）。采用了 `llm-credentials` 的项目按命令给出的 `git show` 采用后两项，否则 `llm-credentials` 指向的步骤和格式就不在仓库里；没有采用 `llm-credentials` 的项目把它们留在外面。`serve-the-coding-agent` 需要时按 `template-adoption` 第 3 步采用，并在该记录的 `## In this repository` 段填 `GUIDANCE`、`COMMANDS`、`ISOLATION`、`TRACE`、`ACCOUNTING` 五项。
3. `llm-credentials` 的 `## In this repository` 段如果有按原 Apply 某一步写的补充，改写为对应 `credential-setup` 的步骤（原第 1–5 步就是新的第 1–5 步）；补充仍写在 `llm-credentials` 的这一段里。
4. `issue-workflow` 的 `## In this repository` 段如果有按 Merge 第 4 步写的“在 dev checkout 里解决冲突”的补充，改到 PR 自己的 worktree 里做；按 “Phased work” 第 3 步写的补充改挂第 4 步。协调者的 agent 名用已有的 `<AGENT_PREFIX>`，不新增槽位。

## v0.1.16 — 2026-10-23

收进下游反馈 #76 与 2026-10-23 这轮 harvest 的三条共享规则（#78–#80）。

- **监督看进度不看存活**（#76）：`long-running-supervision` 新增第 7 步。每次汇报和上一次比较完成数与预算消耗，读每个工作单元最近一次的结果和失败原因，写明没查什么；“进程活着”和“摘要说正常”都不算进度证据；等待一个过程结束要绑在它退出或状态变化上。原第 7 步顺延为第 9 步。
- **给运行中的 Issue session 发后续消息前先看输入行**（#76）：`issue-workflow` 新增 “Messages to a running Issue session”。用 `herdr agent read <name> --source visible` 看输入行，不为空就不发，改走 Issue 评论或请维护者带上；转达维护者的决定只写要达到的结果和约束，命令以项目 skill 为准；指定的做法行不通时按文档路径做、说明偏离并记进 Issue。
- **独立 Issue 并行派出**（#78）：`issue-workflow` 的 Start 之后新增 “Independent Issues run in parallel”，不按先来后到排队，只有真实依赖才等待。
- **速度、并行与效率优化**（#78）：新增共享 memory `speed-and-parallelism-by-measurement`；`long-running-supervision` 新增第 8 步“调度与并发”：独立工作单元并发、交付即触发下游、滚动队列、按实测资源和 provider 健康决定并发、并发度与墙钟和成本分开报告、先消除重复工作。不放宽验证、凭据/安全边界，也不突破明确的花费上限。
- **host 文件归运行用户**（#79）：新增共享 memory `host-files-owned-by-running-user`。项目、agent 和容器留在 host 上的文件、日志、缓存和挂载输出归运行用户；不用 sudo 创建或修改项目文件；清理遇到不属于自己的文件停下来报告；发布和归档前确认归属。
- **可编排的假外部边界**（#80）：新增共享 memory `screen-with-scriptable-fakes`；`long-running-supervision` 第 4 步写明：对 fake 的通过只是真实运行前的便宜筛子，不是完成证据。
- 维护者侧：`template-harvest` 允许一个反馈 Issue 把它来自哪个 adopter 写为来源（`scope: template`，不随升级下发）；模板维护的 Issue 默认用 Pi + DeepSeek 派出（项目 memory，不下发）。

### Upgrading a project from v0.1.15

**Command only.** 运行 `upgrade-template.sh`。它新增三个共享 memory 文件，替换 `issue-workflow` 和 `long-running-supervision` 里 `## In this repository` 段以上的文本，并在 registry 增加三个条目；各项目的 `## In this repository` 段保持不变。下游若在 section 以上自行加过调度、并发或假边界的文字，命令把它报为冲突，保留发布的文本并删去本地副本即可。

## v0.1.15 — 2026-10-22

- **真实运行小而足够**：`issue-workflow` 的 “Issue session rules” 和 `new-agent-prompt.sh` 的交接 prompt 新增同一条规则：真实运行前先判断改动会不会影响系统必须继续做到的事，回归检查已覆盖的改动不需要真实运行；需要的运行用最小的任务、最少的部件和小预算证明本次改动，复用已有证据，除非改动涉及最贵的 provider 否则不用它们；计划和 PR 写明每次运行证明什么、为什么必须跑。它不放宽 “Verify to completion”。
- **CI**：`.github/workflows/template-check.yml` 的 `actions/checkout` 从 v4 升到 v5，去掉 GitHub 对 Node.js 20 的弃用警告。
- **升级目标**：`template-harvest` 第 5 步的升级请求目标总是当前最新版本；落后几个版本的下游一次升到最新，`upgrade-template.sh` 跨过中间所有版本；已有的、目标是旧版本的未关闭升级请求用评论更新到最新版本，不另开 Issue。

### Upgrading a project from v0.1.14

**Command only.** 运行 `upgrade-template.sh`。下游若在 `## In this repository` 段以上自己加过同样的真实运行规则，命令把它报为冲突，保留发布的文本并删去本地副本即可。

## v0.1.14 — 2026-10-22

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
