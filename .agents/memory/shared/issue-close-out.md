---
name: issue-close-out
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issues #34 and #40; Issue #87 (steps left to issue-workflow); Issue #89 (several coordinators); Issue #137 (maintainer workflow revision)
applies_to: repositories that manage Issue worktrees with Herdr, develop from a dev integration branch and merge PRs back into it
---

# Close out an Issue's worktree after its PR merges

## Decision

The coordinator handles PR integration and conflicts in dev, protecting other
writers, existing changes and live runs. Semantic choices needing the maintainer
are escalated. After an authorized merge is verified and remaining duties are
fulfilled or transferred, the coordinator migrates state and retires the
worktree. Idle and merged do not establish completion of outstanding work.

Results that cannot be rebuilt are archived before the merge rather than left in
the migration directory. A live run in the dev checkout holds back a pull or
merge there, and a live task in the worktree, including a container that mounts
it, holds back its close-out; both go to the maintainer.

## Why

Adopters that manage Issues with Herdr independently reached this procedure after a
merged PR left its worktree and branches behind and after conflicting PRs were
resolved ad hoc. Results archived only after the merge changed tracked files too
late, so the archive check moved ahead of the merge. While the link between merge
approval and close-out was implicit, coordinating sessions still paused between
the two to ask (Issue #34). A merge into a checkout that drove a live run left
conflict markers in a module the run imported on its next restart, and the run
failed; a worktree's own monitor command does not see a container that mounts the
worktree, so removing it would remove data the container still refers to
(Issue #40).

Several coordinators may share dev. Issue #137 changed integration ownership:
the coordinator handles the final combined state in dev while protecting
concurrent work; the issue agent is not automatically given cross-Issue duties.

## Apply

Follow Merge and Close-out in
[`../../skills/shared/issue-workflow/SKILL.md`](../../skills/shared/issue-workflow/SKILL.md):
the dev live-run check, the order of the close-out steps, when not to close out,
and what is left to the maintainer.
