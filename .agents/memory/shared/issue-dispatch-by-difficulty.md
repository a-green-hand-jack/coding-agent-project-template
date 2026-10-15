---
name: issue-dispatch-by-difficulty
date: 2026-10-15
source: Issue #26, harvested from a downstream adopter of this template
scope: shared
applies_to: repositories that start Issue agents with the issue-workflow skill
status: active
supersedes: null
superseded_by: null
---

# Dispatch each Issue agent by difficulty and record it in the Issue

## Decision

Before Start, the coordinating session judges the Issue's difficulty by scope,
risk and uncertainty, picks one of four tiers (mechanical, routine, hard,
hardest), and starts the agent with that tier's model and reasoning effort passed
explicitly. The dispatch is recorded in a Dispatch section of the Issue body. A
fallback agent is used only when the primary one is unavailable, and every
re-dispatch is recorded with its reason.

## Why

One fixed agent configuration either wastes the strongest model on mechanical
work or sends risky work (credentials, isolation, concurrency) to a weak one. The
CLI's default model and effort change without notice, so an implicit dispatch
cannot be reproduced. A downstream adopter settled this rule and kept it; the
Issue record makes the choice reviewable when its outcome is judged.

## Apply

Follow Start and Dispatch by difficulty in `.agents/skills/shared/issue-workflow/`,
after filling its tier, effort and fallback slots. When unsure, or when a mistake
is costly, go one tier up. Do not switch to the fallback agent for difficulty or
preference.
