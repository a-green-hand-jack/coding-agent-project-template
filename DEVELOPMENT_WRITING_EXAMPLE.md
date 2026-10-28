# 开发写作的真实中文对照

这是本模板专属 human 示例，不属于下游共享规范。依据维护者认可的
[2026-10-28 案例集](https://github.com/a-green-hand-jack/coding-agent-project-template/releases/tag/writing-cases-20261028)，
保留四类开发文字的历史节选、建议改写和事实待核对状态；共享规则见
[development-writing](.agents/skills/shared/development-writing/SKILL.md)。

案例集代码锚点为 [3bc452396cf24891a6ce1af8ee2b67972d34ec55](https://github.com/a-green-hand-jack/coding-agent-project-template/tree/3bc452396cf24891a6ce1af8ee2b67972d34ec55)。
历史原文是案例集在 2026-10-28 读取的公开内容，Issue、PR 和评论正文可能以后再改；
固定 commit 链接用于核对源码。下文“本次”沿用案例集的采样时间，所有建议均为
编辑示范，未回写历史；测试数字来自旧记录，不能作为本 Issue 新工作树的验收。
具体不足只评价该节选承担的阅读任务，不否定原记录其余部分的价值。

## 1. Issue：从“检查通过”到“完成条件能执行”

### 历史原文：Issue #101 的验收节选

> `bash -n .agents/scripts/*.sh`、模板测试、`diagnose-environment.sh`、`release-doc-audit` 和适用的真实小运行通过。

[阅读 Issue #101](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/101)

**好的部分：**全文已经说明成本策略、agent/model 路由、回收顺序，并给出 dispatch fixture 和资产迁移 fixture 的要求。它不是一个没有范围的任务。

**不足：**这条验收中的“适用的真实小运行”没有定义适用条件、执行入口或完成证据。实现者可能理解为文档变更不适用，审阅者可能理解为必须实际派出一次 agent。两人可以各自合理地解释，却得到不同的完成结论。

### 建议改写：把尚待决定的验收显式化

> 本任务至少完成三档 dispatch 记录 fixture 和状态、资产迁移 fixture，保留命令、退出码与结果。fixture 只能证明记录格式和迁移行为，不能证明实际 agent 派出成功。
>
> 真实小运行要求尚未收敛：派出前需明确本 Issue 是否要求一次实际 agent 启动、消息接收及回收闭环，并确定入口和结果记录。若要求执行，应记录实际 agent/provider/model/effort、启动核对、接收确认和回收证据；若不要求，应在本 Issue 写明理由及未验证范围，经范围负责人确认后再按该标准验收。

这里刻意没有替历史任务补写“真实运行已通过”，也没有直接删除原来的验收项。**文字里未解决的设计决定，不能靠润色伪装成已解决。**这段是针对含糊验收的修复示范；范围已明确的任务不必增加这一轮确认。

### 历史上的好例子：Issue #110

原文先交代具体机制：默认读取去掉样式，CLI 暗色建议看起来就像人的草稿；再说明后果：本应发送的消息被挡住，建议甚至可能被误当成维护者决定。它提出保留 ANSI 样式，并要求两类 fixture：

> 暗色建议允许发送；正常亮度的草稿拒绝发送。

[阅读 Issue #110](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/110)

**为什么好：**问题机制、用户后果、处理规则和验收场景是连起来的。读者无需先翻代码，便能理解这次修改为什么必要。这里评价的是当时 Issue 的写法，不将历史 CLI 样式判断推广为所有版本都成立的事实。

## 2. PR：详细记录也可能掩盖矛盾

### 历史原文：PR #102 与关联 Issue 的记录不同

PR #102 的 Dispatch：

> Pi + `gravarc-router-distill` + `deepseek-v4.1-flash-1017` + high（见 Issue 的 Dispatch 段），无 re-dispatch。

关联 Issue #101 的 Dispatch 则记录了：

> re-dispatched: Pi, `gravarc-router-distill`, `deepseek-v4.1-flash-1017`, high → Claude Code, Anthropic, `sonnet`, high: maintainer preference excludes gravarc router for Herdr worktrees

[PR #102](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/102) · [Issue #101](https://github.com/a-green-hand-jack/coding-agent-project-template/issues/101)

**好的部分：**PR 按成本、路由、回收组织改动，列出 41 个测试通过等历史证据，并明确没有 provider-backed 真实运行。

**不足：**“无 re-dispatch”与 Issue 的改派记录直接冲突。它削弱了执行来源的可信度，也说明正文可能没有随最终状态更新。本次只确认两处公开记录矛盾，不能仅凭文字判定究竟哪个 session 完成了哪些改动。

### 建议改写：先准确描述证据状态

> **执行记录待核对：**Issue #101 记录了由 Pi 改派 Claude Code；本 PR 原 Dispatch 仍写“无 re-dispatch”，两处不一致。最终实施会话及各次运行的归属，需依据当时 session 与验收记录核对后补齐。当前 PR 中的 fixture 和诊断结果，不能单独证明最终执行 agent 的身份，也不证明真实 provider 调用成功。

这是一段诚实的待核对说明。完成核对后，再替换为确切的最终执行记录；不能为了让 PR 看起来完整就猜一个答案。

### 另一种改进：PR #111 应先说行为，再说实现细节

历史正文开头为：

> 更新共享 `agent-communication` skill：要求用 `--format ansi` 检查输入行，识别 `ESC[2m` 包裹的 CLI 暗色建议；建议可被消息替换，不能被当成回答或决定。

[阅读 PR #111](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/111)

这段事实具体、技术信息有用。对不熟悉终端样式的审阅者，可以先补一句前后行为，再解释上述实现：

> 此前，协调者可能把 CLI 自动显示的输入建议误认成人的草稿，导致给空闲会话的消息发不出去。这次更新通信规则：保留样式来区分建议与真实草稿；真正存在草稿时保留输入，并把待传达消息写入关联 Issue 或 PR，避免消息只留在本地。
>
> 本 PR 更新共享 skill 和两类 provider-free fixture。历史记录报告模板测试 50 项通过；这证明了所测规则场景，不等同于所有 CLI 版本的真实端到端通信验收。

**改善点：**先建立审阅者关心的问题，再给技术细节和证据边界。与 PR #102 的事实矛盾不同，这属于阅读顺序优化。

## 3. Comment：新增事实要能改变当前判断

### 历史原文：PR #117 的候选复核评论节选

> 正式 release 正文经 GitHub Markdown API 输出含图像和表格；初始断言错误地只接受无属性的 table 标签，读取输出确认是 table role=table，修正检查后通过，无源内容变更。

[完整评论](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/117#issuecomment-6457287074)

**好的部分：**完整评论给出了精确 head、51 项测试、CI、图像下载和检查边界，没有把 HTML 检查写成完整视觉验收。

**不足：**临时 HTML 断言怎样写错，不影响待合入源码或发布结论，却占据主叙述。评论末尾虽说等待下游检查，但读者要读完较长的过程记录才能知道下一步。

### 建议改写：保持在当时的时间点

> **候选检查通过，等待下游只读检查汇总后发布。**
>
> 检查对象为 PR #117 head `c8c8b2a27bc87fecc49ba760ba35e45ecdd73e5b`。本 head 的模板测试 51 项通过（9.794s）；脚本语法、环境诊断、版本与升级段检查通过，CI 两项 structure 检查通过。
>
> 固定提交的 PNG 可匿名下载且字节一致，正文的 GFM HTML 包含图像和表格。此处只证明 HTML 与资产检查结果，不声称完成正式 Release 页面的视觉检查。
>
> 下一步：原实现会话完成下游只读汇总，协调者核对后执行已授权的正式发布。检查脚本的标签匹配问题已修正，未改变候选源码；诊断细节可折叠保留在此评论中。

这是**候选复核时**的改写，不能混入稍后发布成功的结论。历史后续评论已经记录 v0.1.21 发布；本案例不表示发布仍在等待。

### 同一 PR 的好例子与一个小修正

[正式发布核验评论](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/117#issuecomment-6457379617) 开头直接写“v0.1.21 已发布且非 draft / prerelease”，随后给出 tag/分支指向和最终合并提交的测试结果。这让读者先获得状态变化，再核对证据，值得保留。

另一条 [下游检查评论](https://github.com/a-green-hand-jack/coding-agent-project-template/pull/117#issuecomment-6457372693) 写道：

> 9 条直接下游记录相较当前正式版存在 pin 落后，留待后续升级处理。

它在发布前写入，当时“当前正式版”指 v0.1.20；发布后读者很容易理解成 v0.1.21。建议写成：

> 本轮以 v0.1.20 为对照，9 条直接下游记录的模板 pin 落后。此结果不表示已按后来发布的 v0.1.21 重新检查，也不表示已升级下游。

**改善点：**对照版本写死，结论就不会随着“当前”变化而悄悄改变含义。

## 4. Commit：标题要能从历史列表里认出改动

### 历史原文

```text
docs: clarify agent communication prompt suggestions
```

[提交 b28935d](https://github.com/a-green-hand-jack/coding-agent-project-template/commit/b28935d44133c17b8cd4cc87aaa6eca74ce2ecb1)

本次读取了该提交的实际 diff：它更新通信 skill，并扩展 fixture；核心变化是区分暗色建议与真实草稿，以及将受阻消息写到共享的 Issue/PR 中。

**不足：**“clarify … suggestions”说了主题，却没说澄清后行为有什么不同。后来检索“为什么消息被挡住”，仅看标题难以定位。

### 建议改写

```text
docs: 区分 CLI 输入建议与真实草稿，避免误阻消息

此前不保留样式的输入行读取可能把暗色建议当成人的草稿。
通信规则改为保留 ANSI 样式；真实草稿仍阻止追加消息，
被挡住的消息写入关联 Issue 或 PR，供双方恢复交接。

补充暗色建议和真实草稿两类 provider-free fixture。
关联：#110、#111
```

正文解释动机、保留的约束和测试性质；不用把 PR 的整张验收表复制进来，也不重写已有 Git 历史。

### 历史上的好标题

```text
Make Codex the default template maintenance agent
```

[提交 5dc8715](https://github.com/a-green-hand-jack/coding-agent-project-template/commit/5dc871533bbbc0ce8af4039c738b8ba268869488)

它直接说明最终决定，即使没有 `feat:` 或 `docs:` 前缀，读者也能看懂。中文项目可以表达为“将模板维护的默认 agent 调整为 Codex”。前缀是否统一是格式约定；标题是否说明实际变化才是信息质量。

## 案例阅读边界

PR #102 与 Issue #101 的 Dispatch 冲突仍待依据原始 session、运行记录核对；
本规范不判定最终实施会话。PR #117 的候选检查、稍后的发布结果和以 v0.1.20 为
基线的下游检查分别属于各自时间点。CLI 样式案例描述当时的规则和证据，不代表
每个客户端版本都成立。小改动可以只用一句具体标题和适用检查，不强套长报告。

本文件仅沉淀已认可案例；没有新增运行或发布，也没有进行浏览器视觉检查。
