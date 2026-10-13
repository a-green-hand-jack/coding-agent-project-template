---
name: issue-in-herdr-worktree
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template
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

## Why

Adopters that manage Issues with Herdr independently reached this rule after an
Issue was implemented by branching in the coordinating window. A separate worktree
and session keep each Issue's state, context and branch isolated, and keep the
coordinator free to merge and hand off other work.

## Apply

Follow `start` in `.agents/skills/shared/issue-workflow/`. Do not run
`git switch -c` in the coordinating window. When `HERDR_ENV` is not `1` or Herdr
is unavailable, report the blocker instead of falling back to an in-place branch,
raw `git worktree add`, or a temporary directory.
