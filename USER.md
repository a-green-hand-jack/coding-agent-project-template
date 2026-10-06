# 用户指南

这里描述最终用户如何安装、运行和使用本项目。

当前模板只提供项目骨架；创建新项目后，应在这里补充稳定的用户入口、配置、
环境变量、输出位置和故障处理。不要把 coding agent 的内部规则写在这里，
也不要把项目开发讨论复制到这里。

## 选择模板版本

普通使用从 GitHub 的 **Use this template** 开始，它使用默认分支的最新版本。
需要固定版本时，从 `v0.1.0` 等 release tag 浅克隆，再替换为新项目的 remote；
具体命令见根目录 [README.md](README.md) 的“使用模板版本”。

下游项目发现模板的跨项目缺陷或改进点时，按照
`.agents/skills/shared/template-feedback/` 的说明向模板仓库提交 Issue，附上
模板版本、复现步骤、影响范围和建议的通用修复。

## 改造已有项目

如果已有项目还没有采用本模板，可以把下面的 prompt 交给该项目中的 coding
agent。它会先检查仓库并给出迁移地图；涉及本地规则或产品行为时，等你批准后
才修改：

```text
请使用本仓库采用的 template-adoption skill，把当前项目迁移到
https://github.com/a-green-hand-jack/coding-agent-project-template 的 v0.1.1。
先读取当前仓库的 AGENTS.md、开发文档、git 状态、入口、运行状态和资产布局，
再读取目标模板的 release notes、AGENTS.md 和相关 shared skills。不要替换产品
代码、项目历史、领域文档、现有测试或项目专属 memory/knowledge/skills。
先输出 adopted/adapted/preserved/rejected 的迁移地图、冲突和验收计划，等待
我的批准；批准后在 Issue branch 中实现，并运行 setup、diagnose、public CLI
和适用的 seam checks。最后报告迁移文件、保留内容、证据和未解决风险。
```

## 升级已有模板项目

如果项目已经采用旧版本模板，把下面的 prompt 交给 coding agent。升级必须保留
下游项目自己的产品和定制：

```text
请使用本仓库采用的 template-upgrade skill，把当前项目从登记的模板版本升级到
https://github.com/a-green-hand-jack/coding-agent-project-template 的 v0.1.1。
先检查当前 template registry、git 状态、Issue、memory、knowledge、skills、
资产和 worktree 状态，再比较当前版本与 v0.1.1 的 release notes 和 registry。
先输出逐路径迁移地图，区分 shared addition、required adaptation、local
conflict、obsolete behavior 和 intentionally skipped change；涉及冲突、公开
行为或资产路径时等待我的批准。批准后在 Issue branch 中只应用批准的变化，
更新 CLAUDE.md、AGENTS.md 层级、registry 和模板版本，运行 setup、diagnose、
public CLI、seam checks 及适用的长时运行监督验证，最后报告证据和风险。
```
