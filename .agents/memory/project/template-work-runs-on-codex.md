---
name: template-work-runs-on-codex
date: 2026-10-28
source: maintainer decision in the coordinating session, 2026-10-26; Issue #108; Issue #127 startup capability correction
applies_to: this template repository's Issue dispatch
---

# Template dispatch requires a confirmed choice

## Decision

Codex is a possible recommendation for template work, not an automatic dispatch.
Before each new Herdr worktree, the maintainer confirms the coding agent, exact
model and thinking level. Evaluate cost, task needs and current availability;
never substitute another agent, model or level without confirmation. Reusing an
existing session for a related Issue does not by itself require another choice.
Record the provider and confirmed settings in the Issue's Dispatch section.

## Why

Issue #137 replaces the earlier Codex-first automatic choice with the
maintainer's decision for each dispatch, while keeping cost routing and explicit
settings. Model availability and account capability change; use current
sources and report unknown availability rather than guessing.

## Apply

Follow `issue-workflow` for the confirmation, identity and
[caller isolation](../../skills/shared/issue-workflow/SKILL.md#codex-caller-identity-and-isolation)
checks. For Codex, verify CLI support for `--no-daemon` and record the actual startup mode;
unsupported isolation is a capability gap, not permission to silently omit it.
When Codex is confirmed, pass the confirmed model and settings explicitly using
the supported `-c 'model_provider="<provider>"'` and
`-c 'model_reasoning_effort="<effort>"'` syntax.
Do not change provider client configuration.
