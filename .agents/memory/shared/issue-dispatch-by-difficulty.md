---
name: issue-dispatch-by-difficulty
date: 2026-10-15
source: Issue #26, harvested from a downstream adopter of this template; Issue #87 (steps left to issue-workflow); Issue #137 (maintainer workflow revision)
applies_to: repositories that start Issue agents with the issue-workflow skill
---

# Dispatch each Issue agent by difficulty and record it in the Issue

## Decision

Difficulty, availability and cost inform a recommendation; the current
`issue-workflow` owns confirmation, fallback and recorded dispatch details.

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
recommendation slots and the Dispatch section; availability and fallback are
checked before asking, not substituted for the maintainer's decision.
