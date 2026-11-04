---
name: issue-in-herdr-worktree
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issue #34; Issue #87 (steps left to issue-workflow); Issue #89 (several coordinators); Issue #93 (dependencies); Issue #137 (maintainer workflow revision)
applies_to: repositories that manage Issue worktrees with Herdr and develop from a dev integration branch
---

# Choose direct development or a Herdr worktree for Issue work

## Decision

Choose direct dev or an isolated Herdr worktree according to the task and
checkout state. The current workflow owns confirmation, reuse, ownership and
integration details; see Apply.

## Why

Adopters that manage Issues with Herdr independently reached this rule after an
Issue was implemented by branching in the coordinating window. A separate worktree
and session keep each Issue's state, context and branch isolated, and keep the
coordinator free to merge and hand off other work. The maintainer runs several
coordinators side by side (Issue #89); a claim recorded on the Issue, read with
`gh` next to Herdr's own agent and worktree lists, lets each see what the others
hold without a new tool.

Issue sessions handed off with a request to say "what was not verified", to
report out-of-scope findings instead of fixing them and to keep edits to shared
files small kept ending with a routine unverified list, related defects left in
place and changes narrowed out of caution (Issue #34). Fixing a related defect
met on the way is part of the Issue, not an unrequested feature.

## Apply

Follow Start and its Issue session rules in
[`../../skills/shared/issue-workflow/SKILL.md`](../../skills/shared/issue-workflow/SKILL.md),
and its Shared boundaries when Herdr is unavailable.
