# Shared skills rules

Shared skills must avoid product names, private paths and provider-specific
assumptions. Each skill states what must be adapted in a destination project,
as slots or steps a destination can extend: destinations write their
adaptations only in a trailing `## In this repository` section (see
`template-adoption` step 5). A skill's own text never contains a line that is
exactly `## In this repository`, not even in an example.
Update the content registry when adding, renaming or retiring a shared skill.

`issue-workflow/` owns acceptance write responsibility; `agent-communication/`
owns transport, receipts, receive-time classification, recoverable terminal
summaries and message cadence. Its
`references/acceptance-scenarios.md` reviews their shared boundary without
claiming fixture review proves a real exchange.

`development-writing/` owns the common writing principles and four development
record types; `references/four-cases.md` holds transferable weak/rewrite examples.
Concrete historical cases stay outside shared packages.

`release-doc-audit/` covers release writing, rendered visual review and the
existing consistency audit; its `references/release-types.md` distinguishes
product upgrades, results, milestones/archives and concise releases. Keep
concrete project release examples outside shared packages.

<!-- registry-index:start -->
- [agent-communication](agent-communication/SKILL.md) — Resolve native addresses, reconcile backlog and record distinct delivery/receipt outcomes.
- [asset-lifecycle](asset-lifecycle/SKILL.md) — Adapt asset classes, storage roots and migration evidence.
- [cli-first-operations](cli-first-operations/SKILL.md) — Use the project's public CLI instead of ad-hoc wrappers.
- [credential-setup](credential-setup/SKILL.md) — Set up declared project credentials without copying logins or exposing values.
- [development-writing](development-writing/SKILL.md) — Write Issues, PRs, comments and commits around reader decisions and traceable evidence.
- [issue-workflow](issue-workflow/SKILL.md) — Scope, dispatch, protect acceptance inputs, integrate and close an Issue with explicit ownership.
- [long-running-supervision](long-running-supervision/SKILL.md) — Observe and recover long runs through the product public CLI.
- [project-memory-governance](project-memory-governance/SKILL.md) — Classify, register and migrate development content without losing provenance or authority.
- [release-doc-audit](release-doc-audit/SKILL.md) — Draft readable release narratives and audit rendered output, versions and upgrade paths.
- [template-adoption](template-adoption/SKILL.md) — Adapt the target repository's rules, product paths and acceptance commands.
- [template-feedback](template-feedback/SKILL.md) — Adapt the canonical template URL, labels and upstream Issue fields.
- [template-upgrade](template-upgrade/SKILL.md) — Adapt current and target release tags, local conflicts and migration evidence.
- [worktree-lifecycle](worktree-lifecycle/SKILL.md) — Create, verify and retire isolated worktrees after responsibility and state handoff.
<!-- registry-index:end -->
