---
name: issue-close-out
date: 2026-10-13
source: Issue #18, harvested from downstream adopters of this template; Issues #34 and #40
scope: shared
applies_to: repositories that manage Issue worktrees with Herdr, develop from a dev integration branch and merge PRs back into it
status: active
supersedes: null
superseded_by: null
---

# Close out an Issue's worktree after its PR merges

## Decision

The coordinating session merges the PR from the dev checkout after the maintainer
has approved it on GitHub, and resolves conflicts between open PRs there instead of
asking each Issue session to do so. The maintainer's approval to merge covers the
close-out, so after the merge is verified the coordinating session closes the
worktree out immediately and reports, without asking again: confirm the Issue is
closed and the branch is in `dev`, update local `dev`, migrate `.project/` state
and asset links to the dev checkout with `teardown-worktree.sh --migrate-to`,
remove the worktree with `herdr worktree remove`, then delete the local and remote
branches.

Results that cannot be rebuilt must not stay in the migration directory. They are
archived and registered with the project's archive command, preferably before the
merge.

The dev checkout may itself drive a long-running run. Before pulling or merging
into it, the coordinating session runs the project's monitor command there; a live
run goes to the maintainer and the merge waits.

The coordinating session does not close out, and reports instead, when the PR only
references its Issue and the work continues, when the maintainer asked to keep the
worktree, or when a precondition fails: uncommitted changes, unpushed commits, a
live run in the dev checkout, an agent still working, or a live task in the
worktree. A live task includes every container, running or stopped, that mounts a
path inside the worktree; `inspect-state.sh` lists them when a container runtime is
installed.

When the merged PR changed an image or a test fixture, the close-out also removes
the Docker image tags only that branch used, under the rules in
[`docker-objects-prefixed-and-removed.md`](docker-objects-prefixed-and-removed.md).

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

## Apply

Follow `merge` and `close-out` in `.agents/skills/shared/issue-workflow/`. Handle
only this Issue's worktree. Stop and report at the first failing step; do not use
`--force` or `git branch -D`. Leave semantic conflict choices and the merge commit
push to the maintainer. When no existing command covers an archive, report the gap
and open an Issue instead of writing a glue script.
