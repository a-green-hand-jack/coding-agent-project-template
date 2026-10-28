# 开发者指南

## 开发边界

项目声明的产品树是产品面，默认是 `src/`，声明写在 `AGENTS.md` 的“三个平面”
和 `README.md` 的目录表；`.agents/` 是 coding agent 开发面；`README.md`、
`USER.md` 和本文是 human 面。一个主题只在一个权威位置展开，其他位置链接过去。
运行状态、日志、receipt 和临时产物进入当前 worktree 的 `.project/`，不进入
tracked source，也不写到未知的全局目录。

非代码产品树（例如论文的 `paper/`）同样自包含：只复制产品树本身就能构建，
不读取 `.agents/` 中的任何文件；构建输出和中间文件写入 `.project/`（例如
`.project/build/`），不写回产品树或仓库根目录。

结构性变更和模板采用先明确项目服务谁、交付什么、核心概念和非目标，再给出
现有路径到目标路径的逐项映射，区分产品、开发、human、运行状态和资产。读取
源目录和目标目录的 `AGENTS.md` 指令链与 registry，按稳定产品概念组织路径，
不按实验批次设计通用目录，也不强制迁移已有测试。README 负责定位，USER 负责
使用，本文负责扩展和维护；memory 只保留决定和理由。契约冲突必须显式解决，
不能靠 adaptation 段自行授权；步骤见 `template-adoption` 与 `issue-workflow`。

## Issue、branch 和 PR

较大的工作单元先有 Issue，Issue 先收敛问题、范围、验收方式和风险，再开始实现。
小修小改可以直接在 `dev` checkout 里做，不建 Issue、worktree 或 PR；这类改动包括
文档、注释、memory/索引、拼写、单文件且没有设计决定的小修复，以及运行现有命令做
验收而不改产品代码。拿不准时按大的走；小改动变大或出现设计问题时停下来开 Issue。
小改动同样不自动提交或推送；运行适用的检查，并报告证据。

需要 Issue 的工作单元，从 `dev` 创建 `fix/issue-<N>-<slug>`、`feat/issue-<N>-<slug>`、
`docs/issue-<N>-<slug>` 或 `chore/issue-<N>-<slug>` branch。实现和验证完成后
提交 PR 回 `dev`；`main` 只承载已发布状态。复杂父任务可以显式采用父集成分支：
在父 Issue 登记目标、负责人、子 PR base、最终 dev PR、联合验收与清理责任，
仍通过 Herdr 创建隔离 worktree。子 PR 合入集成分支不等于父任务交付，简单 Issue
仍直接目标 `dev`；完整流程见 `issue-workflow` 的 “Optional parent integration branch”。

分阶段的工作开一个父 Issue，每个阶段一个子 Issue（GitHub sub-issue 关系，父 Issue
列出阶段清单），每个阶段照常走 Issue、worktree 和 PR；做法和 `gh` 命令见
`.agents/skills/shared/issue-workflow/` 的 “Phased work”。Issue、PR 和 human 文档的
工作语言与 Issue 开头段落在 registry 的 `writing:` 声明（同一 skill 的 “Writing
conventions”）；本仓库声明为中文。

Issue、PR、评论与 commit 的阅读职责、正文维护和证据边界统一见
[`development-writing`](.agents/skills/shared/development-writing/SKILL.md)，
四类可迁移正反例在其 references。本仓库后续 commit 信息也使用中文，不强制
Conventional Commits 前缀；下游可在该 skill 的末尾适配段声明自己的 commit 语言
或格式，未声明语言时沿用已有语言，不改变共享英文文本。
[真实中文对照](DEVELOPMENT_WRITING_EXAMPLE.md) 保留已认可案例的历史原文、建议
改写和事实待核对状态，属于本模板示例，下游不复制。范围变更更新 Issue 正文，
最终实现变更更新 PR 标题和正文，重要决定在评论中保留；写作不增加提交或发送授权。

实现依赖与验收依赖分开记录。接口固定且可以独立推进的部分可以提前开发，
但须在上游合并后同步目标分支并完成集成验收；真实 blocked-by 不得绕过，混合
范围需要拆成依赖准确的子任务。执行者负责自己 worktree 的实现、冲突修复和
证据回报；认领 Issue 的协调者负责交付后的依赖重评估、通知、审阅与复核。
等待记录写明事件、责任人、关联 head/run、未完事项和后续动作。通信的提交、
接收确认与任务完成分别记录，具体传输与权限边界见 `agent-communication`。

实现者在实现/验收完成、PR 创建、影响审阅的新 head、阻塞或验收失败，以及职责或
关闭条件变化时，主动向交接中指定的协调者发送带事件 ID、确定版本、证据和未完义务
的回报。发送成功、明确 ACK、实际完成分别记录；没有 ACK 就保留负责人、恢复入口
和有界重试/下一检查条件，不能只在自己的最终回复中宣布交付。没有交付授权时报告
ready-for-review 并等待，通知不授予提交、开 PR、合并或发布权限。
协调者在恢复、接到结果或状态更新、准备结束本轮、合并前及 head 变化后的活动检查点，
先读任务摘要和收据，按接收分类归并已经到达的积压，再决定是否核对 GitHub PR/head。
已被终态证据覆盖的事件默认只留本地处置记录，不新增查询、派发、测试、消息/ACK 或
用户完成汇报；异 ID 同结果也如此。状态未知、矛盾、新职责或用户主动询问才触发必要
核对；实际审阅、合并和新 head 的验证门槛仍须满足。发现漏报的 PR 要按其当前职责
接收并核验证据；旧 head 验收不证明
新 head 已完成。完整触发点见
[`issue-workflow`](.agents/skills/shared/issue-workflow/SKILL.md#delivery-reporting-and-coordinator-reconciliation)，
收据、去重、乱序和恢复规则见
[`agent-communication`](.agents/skills/shared/agent-communication/SKILL.md#delivery-events-and-recovery)。
会话未运行时不承诺持续感知；下次活动检查点恢复，不新增常驻轮询。
任务摘要保留最终版本、已覆盖结果、完成或经 ACK 转移的职责、风险及证据入口，随
现有收据迁移，并在协调者状态中登记可恢复路径。迟到失败、未转移职责和同 ID 内容
冲突必须保留并归并实际增量；用户真正的新指令不受事件去重影响，旧消息里的授权
也不成为新授权。客户端若仍启动空转 turn 或要求可见回复，应单独记录这一限制；
本协议不修改底层消息队列，也不承诺隐藏通知。

协调者和执行者在同一 checkout 上验收前，按
[`验收写入责任`](.agents/skills/shared/issue-workflow/SKILL.md#acceptance-write-responsibility)
登记确定版本（含未提交输入）、负责人、相关写入者、保护路径及允许的输出。所有
相关写入者明确确认暂停后才开始；验收可以写约定的日志和产物，只读评审照常进行。
独立不可变快照保留来源与隔离证据，无需冻结开发 checkout。新修改要求、漂移、
失联或重启都不能默默解冻：先结束或作废旧验收，确认运行停止或隔离，再明确归还
写入责任并由接收方确认。超时不是授权，前后相同 HEAD 也不能排除中途修改后恢复。

按 [`消息节奏`](.agents/skills/shared/agent-communication/SKILL.md#message-cadence)
及时发送关键交接、失败和影响对方下一步的变更；同一检查点、同一版本的结果与
待办合并，普通进度只记本地。收据可以捎带在有内容的消息里，但依赖该交接的动作
仍须等待明确 ACK；ACK 不再要求 ACK，重复事件只在发送方仍有待确认义务时返回
已有收据。不循环催问或心跳，等待期间继续独立工作。
[`场景审阅`](.agents/skills/shared/agent-communication/references/acceptance-scenarios.md)
覆盖失败分支，不能替代授权双方真实暂停、验收、归还及合并结果消息的运行证据。

PR 描述应说明改了什么、为什么改、验收和 CI 要求的每项检查的命令与结果，以及
顺带修复的相关缺陷；只有维护者本人才能完成的步骤写成具体阻塞，说明维护者要做
什么。真实运行、构建和发布证据放在 Issue 或 PR 中，不靠 agent 的自述代替。

Issue 的 Dispatch 段记录派出这个 session 的 agent、provider、model 和 effort。
普通测试、回归检查、文档和机械改动默认用最便宜的 token 来源和模型；只有改动
直接涉及昂贵 provider 的请求格式、权限、模型能力或真实行为时才使用它。廉价
运行仍然必须是真实 provider-backed 运行，不能替代验收需要的能力验证；计划
和 PR 说明每次运行的 agent、provider、model 和 effort、证明了什么、为什么必须
跑，换掉其中任何一项都按 re-dispatch 记录。规则见
`.agents/memory/shared/provider-cost-routing.md`，派出步骤见
`.agents/skills/shared/issue-workflow/` 的 “Dispatch by difficulty”。

开始实现需要 Issue 的工作单元时，使用 Herdr 的原生 worktree 命令从声明目标
（默认 `dev`，子任务可用已声明的父集成目标）创建 Issue branch，并在新 pane
启动独立的 coding-agent session。不要在当前 agent 窗口
直接 `git switch -c`。新 session 的第一步是运行 setup；父 session 可用下面的命令
生成包含 Issue 链接、分支、读取范围和验收要求的初始 prompt：

```bash
bash .agents/scripts/new-agent-prompt.sh 123 fix/issue-123-example
```

第三个可选参数指定已声明的 PR 目标，省略时为 `dev`；该参数不授予创建、提交或
合并权限。
第四个可选参数是 `.project/state/` 下的本地协调者交接文件：包含协调者名字、pane、
原生 session/thread 或无法解析的原因、任务/角色/attempt、回报授权、恢复入口和
下一检查条件。脚本原样附入生成结果；省略时会提示派出前补齐。发送前检查实际生成
内容，私有地址不写入公开 Issue；接收者须先 ACK 范围与授权。

命名使用稳定任务键 `<project>-issue-<N>`：workspace label 追加简短主题，tab
追加 implement / review / tests 等角色，Herdr agent 遵守长度、字符和 live 唯一性
限制；原生 session 支持时采用相同任务键与角色，否则登记 thread ID 映射。重派
保留任务键，记录新 ID 与 attempt，旧会话活着时使用唯一后缀。标识符只取自返回值，
不从显示名推断，也不为改名移动 worktree；完整示例见 `issue-workflow` 的
“Task names and identifiers”。只调整本 Issue 管理的会话。

Herdr 不可用时应报告阻塞，不能改用当前窗口直接实现。

## Worktree 生命周期

每个 worktree 都是独立的工作单元，必须拥有自己的状态根、运行目录、输出目录
和资产入口。创建 worktree 后，在其中运行：

```bash
bash .agents/scripts/setup-worktree.sh
```

setup 会写入 `.project/home` 和 `.project/worktree.env`，创建本地状态目录，
检查工具和资产 manifest，并记录当前 branch、commit 和路径。不要手工复用另一个
worktree 的 `.project/`。具体项目可以提供可执行的
`.agents/scripts/setup-project.sh` hook；setup 会在基础初始化后调用它。

合并 PR 后不要直接删除目录。回收顺序固定为“停进程 → 迁移状态和资产 → 确认
没有唯一副本 → 移除 worktree 和 branch”：

1. 先核对 Issue/PR 承诺、`.project/state/` 等待记录和后台运行。`idle` / `done`
   只描述前台会话，PR 已合并也不代表后台验收、审计或承诺已完成。仍承担这些职责
   时保留 worktree，直到完成，或在授权下明确移交责任、状态和产物并得到接收确认。
   不得为回收而默认终止承担验收的运行。职责结清后，确认 agent session 已
   `idle` 或 `done`。用项目自己的 monitor
   命令列出这个 worktree 启动的运行，逐个通过项目自己的 stop 命令停止，直到
   monitor 不再列出任何运行。不要用通用的 `pkill`、`killall` 或按名字匹配的
   进程清理：只有项目自己的 stop 命令可以停止进程。本模板没有产品运行，所以
   仓库里没有 stop 命令；有产品的项目在 `issue-workflow` 的 `<MONITOR_CMD>` /
   `<STOP_CMD>` 槽位登记自己的命令。
2. 再查 monitor 看不到的部分：`.project/runs/` 记录的进程身份是否都已消失，
   以及 `.agents/scripts/inspect-state.sh` 列出的挂载这个 worktree 的容器（运行中
   或已停止）。仍有运行、无法停止或无法确认时停下来报告，不继续回收。
3. 确认没有运行后迁移。先运行：

   ```bash
   bash .agents/scripts/teardown-worktree.sh --migrate-to /path/to/canonical-project
   ```

   该命令会检查 ignored state、复制 `.project/state`、`runs`、`artifacts`、
   `manifest`、`migrate-project.rules` 标记 `copy` 的条目和资产软链接，逐项校验
   并写入迁移记录；它不会自动删除 worktree。`setup-project.sh` 在 `.project/`
   下创建的条目，在 `.agents/scripts/migrate-project.rules` 里逐行写明迁移方式
   （`NAME|ACTION|WHY`，ACTION 为 `copy`、`drop` 或 `login`），否则 teardown 会
   停下来要求决定。`NAME` 可以是 shell 通配符，一行管一类文件，例如
   `plan-*.md|copy|`；通配符不能含 `/`、不能是 `login`、不能匹配模板自己处理的
   条目，同名的精确规则优先于通配符。Issue session 自己的工作文件放在
   `.project/state/`，teardown 总会复制它，不需要规则。确认迁移输出里的
   `verified:` 覆盖上述条目和每个资产链接、资产软链接在 dev checkout 可解析、
   没有唯一副本留在旧目录后，再用 worktree 管理工具销毁 worktree 和 branch。

## 环境变量与资产

`.env.example` 只声明变量名、用途和文件路径约定，不包含秘密。项目需要的凭据
按名字登记在根目录受跟踪的 `credentials.yaml`：需要设备清单 `inventory.yaml`
的哪些行、工具用什么名字读取、给哪个沙箱或岗位、必需还是可选。setup 运行
`bash .agents/scripts/probe-credentials.sh --check`，对缺行、空占位和未设置的
必需凭据报错；diagnose 运行只读探测，逐个报告 `credential <name>: ok | failed |
not-probed`。任何输出都不包含凭据值；格式和检查见
`.agents/knowledge/shared/credential-inventory.md`，规则见
`.agents/memory/shared/llm-credentials.md`，操作步骤见
`.agents/skills/shared/credential-setup/`。

大资产放在外部存储时，在仓库内的 `assets/` 登记稳定逻辑入口，并在
`assets/MANIFEST.yaml` 登记：用途、来源、版本、checksum、可重建性和删除 worktree
前的保留要求。机器相关的软链接写在被忽略的 `.project/assets.links` 中，由 setup
创建；不要提交软链接或其绝对目标路径。

## Memory 与 knowledge

`.agents/memory/` 记录长期决策，`.agents/knowledge/` 记录有来源和刷新条件的
事实。两个目录的 `AGENTS.md` 只包含规则和简短索引；正文按主题拆成独立 Markdown
文件，放入 `shared/` 或 `project/`，并使用对应的 `ENTRY_TEMPLATE.md` front
matter。新增或迁移条目时同步更新分组索引和 `content-registry.yaml`。

## 分支模型与仓库可见性

模板采用 `dev` 集成、`main` 发布的双分支模型。新仓库第一次 setup 会在可用的
GitHub CLI 环境中幂等创建并推送 `dev`，并把 GitHub 默认分支设为 `dev`；也可以
显式运行 `bash .agents/scripts/init-branches.sh`。诊断会报告缺失项和修复命令。

采用模板时优先选择 **Private**，直到产品、筛选记录和实验结果准备公开。公开前
检查凭据、私有数据、Issue/PR 内容、日志和本机路径；模板仓库本身是公开的，向它
提交的 Issue 会显示下游仓库名称和描述，因此模板反馈只能包含通用、脱敏的复现
信息，并只说明下游是私有还是公开仓库；仅当下游公开且其维护者同意时才写出仓库名称。

## 验证策略

测试只用于验证真实风险、历史缺陷和生产接缝。不为 coverage 机械增加测试。
产品完成至少需要经过适用的 public entrypoint、真实构建或运行路径；局部测试
通过不能替代产品验收。

```bash
bash .agents/scripts/diagnose-environment.sh
bash .agents/scripts/inspect-state.sh
```

模板仓库自己的脚本测试是 `.agents/tests/test_template_*.py`（只属于模板，下游
不复制）：

```bash
python3 -m unittest discover -s .agents/tests -p 'test_template_*.py'
```

合并和发布只看本地检查：上面这些命令就是本仓库的 `issue-workflow`
`<LOCAL_CHECK>`（槽位默认值就是本节的验证策略），也是
`.github/workflows/template-check.yml` 的步骤：`bash -n .agents/scripts/*.sh`、
`setup-worktree.sh`、`diagnose-environment.sh`，以及（只在模板里）
`test_template_*.py`。协调者在 PR 的 worktree 里、PR 最新的提交上跑它，把提交
SHA、每条命令的结果和 CI 状态（通过、失败、没运行）写成 PR 评论；发布 PR（`dev`
→ `main`）也一样。本地检查全部通过并经维护者批准即可合并，CI 只在 PR 上标记，
不等它，也不因它没运行（例如 Actions 因计费不能启动）而停下；CI 失败而本地通过
时写进评论和报告，由维护者决定要不要查。

`.github/workflows/template-check.yml` 只在指向 `dev`、`main` 的 PR 和推送到
`dev`、`main` 时运行，同一 ref 的新运行取消旧运行，并有超时。它是可选内容：
`issue-workflow` 的 `<CI>` 为 `no` 的项目不采用它，模板升级也不会把它加回来；
`<LOCAL_CHECK>` 不论 `<CI>` 是什么都要填。

## 产品构建与安装骨架

需要 Python 包、容器或安装入口的项目从根目录的 `pyproject.toml`、`Dockerfile`
和 `install.sh` 占位文件开始，替换项目名、依赖、基础镜像和 public entrypoint。
包清单只从产品树（默认 `src/`）收集产品代码；`.dockerignore` 排除 `.agents/`、
`.project/`、`AGENTS.md`、`CLAUDE.md` 和开发文档。非 Python、非代码或不需要镜像的
项目可以删除或改写对应骨架，并在 adoption/upgrade 迁移地图中记录取舍。

## 与模板的关系

本仓库是 `coding-agent-project-template` 的模板仓库本身；当前模板版本记录在
`.agents/content-registry.yaml` 的 `template.version`，模板自己的发布历史在
`RELEASE_NOTES.md`。

从模板创建的项目在自己的 registry 里记录它采用的 `template.repository` 与
`template.version`，并保留自己的 `RELEASE_NOTES.md`，不复制模板的发布历史。
升级到新的模板版本用 `.agents/skills/shared/template-upgrade/`：
`bash .agents/scripts/upgrade-template.sh [--check] <TAG>` 按 registry 完成机械部分，
跨过的每个版本在 `RELEASE_NOTES.md` 的升级段都标为 **Command only.** 且没有冲突
时走轻量路径，否则以命令的计划为起点走完整流程。模板每个版本的 release notes
都要有 `### Upgrading a project from <上一个 tag>` 段，以 **Command only.** 开头
或列出手动步骤（`release-doc-audit` 检查）。发现模板本身的
缺陷或缺失能力时用 `.agents/skills/shared/template-feedback/` 向上游开 Issue；
模板维护者主动收集下游已沉淀的通用实践用 `.agents/skills/template-harvest/`
（只属于模板仓库，下游不复制）。只有 URL 是项目专用的，其余规则通用。

派生模板是从本模板建立、自己又作为模板供其他项目使用的仓库，例如论文模板
[`paper-agent-project-template`](https://github.com/a-green-hand-jack/paper-agent-project-template)。
它的 registry 用 `template` 记录它自己和它自己的版本，并用 `template.upstream`
记录它所跟随的上游模板：

```yaml
template:
  repository: <派生模板自己的仓库 URL>
  version: <派生模板自己的 release tag>
  upstream:
    repository: https://github.com/a-green-hand-jack/coding-agent-project-template
    version: <它跟随的本模板 release tag>
```

| 仓库 | `template.repository` / `template.version` | `template.upstream` |
| --- | --- | --- |
| 本模板 | 本模板，当前模板版本 | 无 |
| 从本模板创建的项目 | 本模板，采用的 tag | 无 |
| 派生模板 | 派生模板自己，它自己的 release | 本模板和它跟随的 tag |
| 从派生模板创建的项目 | 派生模板，采用的 tag | 无 |

一个仓库跟随的模板是 `template.upstream`（有这一字段时），否则是 `template`
（本模板自身除外）。`template-adoption` 写入这一字段，`template-upgrade` 从它读取
升级的源版本并把它更新到目标 tag，`template-feedback` 用它把派生模板从上游继承的
缺陷路由到上游仓库。从派生模板创建的项目只记录该派生模板，删除复制来的
`upstream` 块；它的反馈先到派生模板，由派生模板判断是否转给上游。

## 发布

发布正文面向读者独立讲清楚项目背景、比较起点、核心变化、证据与边界，以及如何
使用、升级或获取成果。按用户影响组织内容，用有图注的流程图、对照表或真实
结果帮助理解；参考资料保留 Issue、PR、前版、固定代码和完整 compare 链接，
正文不能依靠读者点开它们才能理解。不同发布对象和小发布的取舍见
[`release-doc-audit`](.agents/skills/shared/release-doc-audit/SKILL.md) 及其类型参考。

本仓库的[中文图文发布草稿](RELEASE_EXAMPLE.md) 展示 v0.1.20 到 PR #114 的实际
变化，图源和静态图在 `.github/release-examples/`；它们属于模板专属 human 示例，
下游不复制，也不代表新版本已经发布。共享 skill 保持英文，下游在末尾适配段
填写受众、发布面、图像托管、仓库 URL、release notes 归属与 `RELEASE_HEADING`。

发布前检查：工作树干净、文档与行为一致、资产 manifest 可解析、环境入口可用、
适用的回归和真实运行证据已记录。运行
`.agents/skills/shared/release-doc-audit/`，处理或记录每个文档审计发现。发布只
从 `main` 或 release branch 进行，并更新下游项目自己的 `RELEASE_NOTES.md`；
模板仓库的 `RELEASE_NOTES.md` 只记录模板版本，不作为下游版本记录。
同时检查目标发布面的实际渲染、窄屏可读性和图链接；不支持内嵌图时使用可访问的
静态图。仅本地准备时记录预览面和托管检查缺口，不为预览而发布。历史验收与最终
候选验证分别说明，保留 `### Upgrading ...` 和 **Command only.** / 编号手动步骤
的机器读取协议；草稿不改历史 release、版本号或 registry 的模板版本。

模板仓库发布前还要运行 `.agents/skills/template-harvest/`，收集下游已沉淀的通用
实践，并把每个候选的分类与 Issue 记录下来；没有可访问的下游时在发布记录中写明。
该 skill 只属于模板仓库，下游项目不复制，也不在自己的发布清单中引用。

## CLI 与长时运行监督

项目的 setup、run、status、monitor、checkpoint、resume、artifact 和 release
操作应通过一个稳定的 public CLI 暴露。不要让 coding agent 或 human 通过私有
Python 函数、临时 provider SDK 或第二套脚本绕过产品入口。

如果产品运行时间超过一个交互回合：

- 在 `.project/runs/` 记录 worktree、状态根、配置、版本、输出目录和进程身份；
- 在独立的 Herdr pane、tmux 或 service 中运行，不占住 coding agent 的前台上下文；
- 提供一个只读 `status` 或 `monitor` 入口，展示进度、最后活动、错误、产物和恢复提示；
- 将结构化 receipt 和日志写进当前 worktree 的状态根；
- 明确定义 stop、checkpoint、resume、retry 和 terminal failure；
- 不修改活动运行下的代码：代码修改和合并在另一个 worktree 进行；运行中的
  checkout 里的脚本必须替换时，先写新文件再 rename 覆盖，不原地编辑；向该
  checkout pull 或 merge 前先用 monitor 入口确认没有活动运行；
- 将实现完成、运行验收和最终产物验收分开报告。

通用原则和最小操作清单见 `.agents/skills/shared/cli-first-operations/` 与
`.agents/skills/shared/long-running-supervision/`。
