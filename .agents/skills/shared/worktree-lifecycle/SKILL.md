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
5. Stop what the worktree started, before anything is migrated or removed.
   Confirm the coding agent session is `idle` or `done`. When the project has a
   monitor and a stop command, run the monitor in the worktree and stop every run
   it lists through the stop command, then run the monitor again until it lists
   none. Only the project's own stop command may stop a process: never `pkill`,
   `killall`, `fuser -k` or a name pattern, so a process this worktree did not
   start is never touched. Then check what the monitor does not see: the process
   identities recorded under `.project/runs/` and the containers that mount the
   worktree (`.agents/scripts/inspect-state.sh` lists them, running or stopped).
   A run that cannot be stopped, a recorded process still running, a container
   that mounts the worktree or a state that cannot be confirmed stops the
   retirement and goes to the maintainer.
6. Migrate once nothing runs. Run
   `.agents/scripts/teardown-worktree.sh --migrate-to <canonical-project>`. It
   inspects state, then copies
   `.project/state`, `runs`, `artifacts`, `manifest`, the entries
   `migrate-project.rules` marks `copy` and the untracked asset links into the
   canonical checkout, verifies each copy and prints the migration path. Confirm
   the `verified:` line covers those entries and every asset link, and that
   results that cannot be rebuilt are archived to external storage.
7. Verify the canonical project holds the migrated records, that the asset links
   resolve there, and that no unique asset or result remains only in the retiring
   worktree. Only then remove the worktree and branch with the worktree manager.

This skill does not delete worktrees and does not grant permission to destroy
data. It provides the procedure; the repository's lifecycle policy decides who
may execute it.
