---
name: issue-dispatch-by-difficulty
date: 2026-10-15
source: Issue #26, harvested from a downstream adopter of this template; Issue #87 (steps left to issue-workflow)
scope: shared
applies_to: repositories that start Issue agents with the issue-workflow skill
status: active
supersedes: null
superseded_by: null
---

# Dispatch each Issue agent by difficulty and record it in the Issue

## Decision

Each Issue agent is started with an agent kind, provider, model and reasoning
effort chosen for the Issue's difficulty and passed explicitly, never the CLI's
default, and the choice is recorded in the Issue. The cheapest source and model
that can judge the work is the default for mechanical and routine Issues; an
expensive provider is used only when the change concerns that provider itself
(see [`provider-cost-routing.md`](provider-cost-routing.md)). A fallback agent
stands in only when the primary one is unavailable, and every re-dispatch is
recorded with its reason.

## Why

One fixed agent configuration either wastes the strongest model on mechanical
work or sends risky work (credentials, isolation, concurrency) to a weak one. The
CLI's default model and effort change without notice, so an implicit dispatch
cannot be reproduced. A downstream adopter settled this rule and kept it; the
Issue record makes the choice reviewable when its outcome is judged.

## Apply

Follow Start and Dispatch by difficulty in
[`../../skills/shared/issue-workflow/SKILL.md`](../../skills/shared/issue-workflow/SKILL.md),
after filling its agent-kind, provider, model-selection, tier, effort and
fallback slots: the four tiers, when to go a tier up, how a tier's series is
resolved to a model that is usable now, the Dispatch section and the fallback
and re-dispatch lines.
