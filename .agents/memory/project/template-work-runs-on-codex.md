---
name: template-work-runs-on-codex
date: 2026-10-26
source: maintainer decision in the coordinating session, 2026-10-26; Issue #108
scope: project
applies_to: this template repository's Issue dispatch
status: active
supersedes: previous Pi-based template maintenance dispatch decision
superseded_by: null
---

# Template work runs on Codex first

## Decision

Template maintenance is dispatched to Codex first, using the OpenAI/Codex
model family. Choose the Issue's difficulty tier, then resolve the newest
usable Codex model for that tier at dispatch time: list what the Codex CLI and
account currently offer, discard models that are retired, unavailable, out of
quota, incapable of the work or excluded, and record the concrete provider,
model and effort in the Issue's Dispatch section. The tier and cost-routing
rules remain in force: routine and mechanical work use the cheapest usable
source and model, while harder or riskier work moves up a tier.

Claude Code and Pi remain available as fallbacks, in that order, only when
Codex or its provider is unavailable or no usable model remains for the tier.
Any fallback or later change of agent, provider, model or effort is recorded as
a re-dispatch. The generic `issue-workflow` preference order is therefore
`codex, claude, pi`, while dynamic model resolution and the existing fallback
rules remain the source of the concrete dispatch.

## Why

Codex is the first default for maintaining this template, so the project
memory must agree with the shared `issue-workflow` order instead of overriding
it with a stale Pi-specific choice. Keeping the tier and cost rules means a
small documentation or index change does not consume a stronger model than it
needs, while a hard Issue can still move to a stronger tier or fallback agent.
Resolving the model at dispatch time keeps the record current as the Codex
model catalog, entitlements and quotas change; the Issue remains the audit
record of what actually ran.

## Apply

Start the Issue session with Codex and explicit model and effort arguments.
Resolve `<newest usable Codex model>` from the models the Codex CLI and account
currently offer before starting, then record the resolved string in the Issue's
Dispatch section:

```bash
herdr agent start tpl-issue-<N> --kind codex --pane <pane> -- \
  --model <newest usable Codex model> \
  --reasoning-effort <effort>
```

Map the selected tier's effort onto the Codex CLI's accepted values. If Codex
is unavailable, re-dispatch to Claude Code and then Pi with each fallback's
own provider, model and effort arguments. Keep the existing `issue-workflow`
model-series resolution, cost routing, difficulty tiers and re-dispatch
history; do not pin a Codex model version or change provider client
configuration.
