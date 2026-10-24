---
name: issue-in-herdr-worktree
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issue #34; Issue #87 (steps left to issue-workflow); Issue #89 (several coordinators); Issue #93 (dependencies)
scope: shared
applies_to: repositories that manage Issue worktrees with Herdr and develop from a dev integration branch
status: active
supersedes: null
superseded_by: null
---

# Implement each Issue in its own Herdr worktree and agent session

## Decision

Each Issue is implemented in its own worktree, created from `dev` with Herdr's
native worktree command, by its own coding-agent session in that worktree's
pane. The maintainer talks to that session there, and that session opens the PR.
Several coordinator sessions may share the dev checkout, each claiming one Issue
with its sub-Issues in the Issue's Dispatch section and dispatching its
worktrees; an Issue another coordinator claimed is left alone. A coordinator
never implements an Issue by switching branches in its own window, and when
Herdr is unavailable it reports the blocker instead of falling back. An Issue
starts only when it has no open blocker; what it waits for is recorded as
GitHub's blocked-by, also across coordinators, and every Issue starts from the
latest `dev`, never from another Issue's unmerged branch.

The handoff gives the Issue session working rules that do not narrow: it
verifies to completion, fixes the defects it meets that block or relate to the
Issue, does not narrow its change to avoid conflicts with parallel worktrees
(the claiming coordinator resolves them at merge, in this worktree), and knows
that the merge approval covers the close-out.

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
