---
name: issue-close-out
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issues #34 and #40; Issue #87 (steps left to issue-workflow); Issue #89 (several coordinators)
scope: shared
applies_to: repositories that manage Issue worktrees with Herdr, develop from a dev integration branch and merge PRs back into it
status: active
supersedes: null
superseded_by: null
---

# Close out an Issue's worktree after its PR merges

## Decision

The coordinator that claimed the Issue merges its PR after the maintainer has
approved it on GitHub. When the PR conflicts with its current declared target
(normally `dev`, optionally a parent's integration branch), that
coordinator resolves the conflict in the PR's own worktree, itself or through the
Issue session, and pushes before merging; the shared dev checkout is only
fast-forwarded with `git pull --ff-only`. Mechanical conflicts keep both sides;
semantic ones go to the maintainer. The maintainer's approval to merge covers the
close-out: after the merge is verified and remaining responsibilities are
fulfilled or explicitly transferred under authorization with acknowledgement,
the coordinator retires the worktree and its branches and reports without
asking again. Idle and merged are not evidence that background acceptance,
pending audits or promised follow-ups are complete.

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

The maintainer works with several coordinator sessions in the dev checkout at
once, each claiming one Issue (Issue #89). Resolving conflicts in that shared
checkout let one coordinator's half-done merge break another's pull, so each
coordinator resolves its own PR's conflicts with `dev` in that PR's worktree.

## Apply

Follow Merge and Close-out in
[`../../skills/shared/issue-workflow/SKILL.md`](../../skills/shared/issue-workflow/SKILL.md):
the dev live-run check, the order of the close-out steps, when not to close out,
and what is left to the maintainer.
