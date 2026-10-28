---
name: worktree-lifecycle
description: Create, initialize, migrate and retire one isolated project worktree.
---

# Worktree lifecycle

Use this skill when starting parallel work, handing an Issue to another coding
agent, or preparing a merged branch for removal.

1. Create the worktree through Herdr's native worktree command from the
   Issue's declared target and with the Issue branch name: normally `dev`, or
   the parent integration branch recorded by `issue-workflow`. Start a new pane
   there and launch an independent coding-agent session; do not implement the Issue
   by switching branches in the parent session. If Herdr is unavailable, report
   the blocker instead of falling back to an in-place branch.
2. Enter the returned worktree and run `.agents/scripts/shared/setup-worktree.sh`.
   The parent session can generate the handoff with
   `.agents/scripts/shared/new-agent-prompt.sh ISSUE [BRANCH] [TARGET_BASE]`.
3. Confirm the `.project/home` marker, branch, state root, output directory and
   asset links all belong to this worktree. Do not reuse another worktree's state.
   Verify the task-key/role/attempt mapping and actual workspace, tab, agent and
   native session names/IDs from `issue-workflow`; keep the returned path rather
   than moving the worktree to match a display name.
4. Keep the coding agent session in the worktree that owns the Issue. The parent
   session does not edit that worktree after handing it off.
5. Reconcile outstanding responsibilities before stopping or removing anything.
   Check the Issue/PR commitments, `.project/state/` wait records, background
   jobs and `.project/runs/`, even when the foreground agent is `idle` or `done`
   or the PR is merged. A background acceptance run or pending audit retains
   this worktree until fulfilled, or explicitly transferred under authorization
   with a named owner, acknowledgement and accessible state/results. Do not
   terminate it merely to retire the worktree. A child merge into a parent
   integration branch does not finish the parent. Follow `issue-workflow` for
   the delivery and obligation gate.
   Once no outstanding duty depends on this session or its runs, stop what the
   worktree started before migration. Confirm the coding agent session is
   `idle` or `done`. When the project has a monitor and a stop command, run the
   monitor in the worktree and stop every run
   it lists through the stop command, then run the monitor again until it lists
   none. Only the project's own stop command may stop a process: never `pkill`,
   `killall`, `fuser -k` or a name pattern, so a process this worktree did not
   start is never touched. Then check what the monitor does not see: the process
   identities recorded under `.project/runs/` and the containers that mount the
   worktree (`.agents/scripts/shared/inspect-state.sh` lists them, running or stopped).
   A run that cannot be stopped, a recorded process still running, a container
   that mounts the worktree or a state that cannot be confirmed stops the
   retirement and goes to the maintainer.
6. Migrate once nothing runs. Run
   `.agents/scripts/shared/teardown-worktree.sh --migrate-to <canonical-project>`. It
   inspects state, then copies
   `.project/state`, `runs`, `artifacts`, `manifest`, the entries
   `migrate-project.rules` marks `copy` and the untracked asset links into the
   canonical checkout, verifies each copy and prints the migration path. Confirm
   the `verified:` line covers those entries and every asset link, and that
   results that cannot be rebuilt are archived to external storage.
7. Verify the canonical project holds the migrated records, that the asset links
   resolve there, and that no unique asset or result remains only in the retiring
   worktree. Only then remove the worktree and branch with the worktree manager.

## Recovery when the workspace is already closed

The Git worktree record is authoritative for whether a worktree still exists;
an absent Herdr workspace is not evidence that the worktree was removed. When
`herdr worktree list --workspace "$HERDR_WORKSPACE_ID"` shows the Issue branch
with an empty `open_workspace_id`, capture its path and branch, confirm the
path's `git rev-parse --git-common-dir` belongs to this repository, then reopen
that exact path without focusing it:

```bash
herdr worktree open --workspace "$HERDR_WORKSPACE_ID" --path <worktree> --no-focus
herdr worktree list --workspace "$HERDR_WORKSPACE_ID"
```

Use the returned workspace id only after confirming it is for the Issue path
and is not the canonical workspace. Then run the normal order: reconcile
outstanding obligations, confirm the agent is idle/done, stop eligible project
runs, inspect recorded processes and mounted containers, migrate and verify
`.project/state`, runs, artifacts, manifest and
asset links, confirm no unique copy remains, and only then run
`herdr worktree remove --workspace <reopened-workspace>`. Finally verify the Git
worktree list, local branch, remote branch and canonical branch state. Never
replace this recovery with `git worktree prune`, a raw `git worktree remove`,
or a generic process killer. If reopening fails or the path no longer resolves,
stop and preserve the exact Herdr/Git output for the maintainer; do not delete
the Git record or guess that migration happened.

This skill does not delete worktrees and does not grant permission to destroy
data. It provides the procedure; the repository's lifecycle policy decides who
may execute it.
