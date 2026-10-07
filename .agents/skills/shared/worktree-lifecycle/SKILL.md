---
name: worktree-lifecycle
description: Create, initialize, migrate and retire one isolated project worktree.
---

# Worktree lifecycle

Use this skill when starting parallel work, handing an Issue to another coding
agent, or preparing a merged branch for removal.

1. Create the worktree through Herdr's native worktree command from the
   integration branch and with the Issue branch name. Start a new pane there
   and launch an independent coding-agent session; do not implement the Issue
   by switching branches in the parent session. If Herdr is unavailable, report
   the blocker instead of falling back to an in-place branch.
2. Enter the returned worktree and run `.agents/scripts/setup-worktree.sh`.
   The parent session can generate the handoff with
   `.agents/scripts/new-agent-prompt.sh ISSUE [BRANCH]`.
3. Confirm the `.project/home` marker, branch, state root, output directory and
   asset links all belong to this worktree. Do not reuse another worktree's state.
4. Keep the coding agent session in the worktree that owns the Issue. The parent
   session does not edit that worktree after handing it off.
5. Before retirement, run `.agents/scripts/teardown-worktree.sh --migrate-to
   <canonical-project>`. Inspect ignored state and migrate durable records and
   asset links before the worktree manager removes the directory and branch.
6. Verify the canonical project has the migrated records and no unique asset
   remains only in the retiring worktree.

This skill does not delete worktrees and does not grant permission to destroy
data. It provides the procedure; the repository's lifecycle policy decides who
may execute it.
