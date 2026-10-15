---
name: issue-in-herdr-worktree
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issue #34
scope: shared
applies_to: repositories that manage Issue worktrees with Herdr and develop from a dev integration branch
status: active
supersedes: null
superseded_by: null
---

# Implement each Issue in its own Herdr worktree and agent session

## Decision

The coordinating session creates the Issue branch from `dev` with Herdr's native
worktree command, starts a new coding-agent session in the new pane, runs
`setup-worktree.sh` there and delivers the handoff prompt. The maintainer talks to
that session in its pane, and that session opens the PR. The coordinating session
does not implement the Issue by switching branches in its own window.

The handoff gives the Issue session four working rules. It verifies to
completion: it runs every check the acceptance and CI call for and reports one
definite result with evidence, naming only a step the maintainer alone can
perform as a blocker. It fixes the defects it meets that block or relate to the
Issue in the same worktree; only unrelated, larger problems go to a separate
Issue. It treats parallel worktrees as expected and does not narrow its change
to avoid conflicts, which the dev checkout resolves at merge. It knows that the
merge approval covers the close-out, so results that cannot be rebuilt are
archived before the merge.

## Why

Adopters that manage Issues with Herdr independently reached this rule after an
Issue was implemented by branching in the coordinating window. A separate worktree
and session keep each Issue's state, context and branch isolated, and keep the
coordinator free to merge and hand off other work.

Issue sessions handed off with a request to say "what was not verified", to
report out-of-scope findings instead of fixing them and to keep edits to shared
files small kept ending with a routine unverified list, related defects left in
place and changes narrowed out of caution (Issue #34). Fixing a related defect
met on the way is part of the Issue, not an unrequested feature.

## Apply

Follow `start` and its Issue session rules in
`.agents/skills/shared/issue-workflow/`; `new-agent-prompt.sh` prints the rules
into every handoff, and the Issue-specific section never narrows them. Do not run
`git switch -c` in the coordinating window. When `HERDR_ENV` is not `1` or Herdr
is unavailable, report the blocker instead of falling back to an in-place branch,
raw `git worktree add`, or a temporary directory.
