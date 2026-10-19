---
name: resolve-real-paths-before-moving
date: 2026-10-19
source: Issue #59, harvested from a downstream adopter of this template
scope: shared
applies_to: any move, copy-then-delete, replacement or symlinking of a directory, by an agent or a script
status: active
supersedes: null
superseded_by: null
---

# Resolve real paths before moving a directory

Related: [`../../skills/shared/asset-lifecycle/SKILL.md`](../../skills/shared/asset-lifecycle/SKILL.md)
(retiring and migrating assets) and
[`llm-credentials.md`](llm-credentials.md) (login directories are never moved
or copied).

## Decision

Before moving a directory, copying it and deleting the source, replacing it, or
turning it into a symlink, prove that source and destination are two different
places holding two different data sets:

1. **Resolve both paths at every level.** `readlink -f` each path, which
   resolves every component, and compare device and inode
   (`stat -L -c '%d:%i'`). List the symlinks inside the source
   (`find -P <src> -type l`) and resolve them too.
2. **Stop on overlap.** When the two resolve to the same directory, when one
   contains the other, or when a link inside one points into the other, stop and
   report. There is nothing to move.
3. **Verify two different data sets.** A file count, a byte total or
   `rsync --checksum` only means something after step 1 showed two different
   directories. The same checks run against one directory twice always agree.
4. **Confirm space will be freed.** Before deleting the source, read what it
   holds on its own filesystem (`du -sx` on the resolved path) and that
   filesystem's free space (`df -P`). Deleting a real copy frees about that much
   there; if it would free nothing, the source is not a copy.
5. **Copy, verify, then let a person choose.** Prefer copying to moving. After
   the copy is verified, report both resolved paths and the evidence, and let
   the maintainer choose which copy to delete. An agent does not delete the
   source on its own.
6. **Back up an unrecoverable asset first.** An asset that cannot be rebuilt
   needs a second verified copy in another place before any copy of it is
   deleted.

## Why

An adopter moved data to another disk while the source path was already a
symlink to the destination. The copy was a no-op. Every check agreed because it
compared the directory with itself, and the following delete removed the only
copy. Free space did not change, which would have shown the problem before the
delete. The same failure appears whenever a path, a parent directory or a
nested entry is a link: renamed checkouts, asset links, mounted volumes.

## Apply

Run steps 1 and 2 before the first write, step 3 after the copy, and steps 4 to
6 before any delete. Report the resolved paths, the device and inode pair and
the space figures with the result. A script that moves or replaces directories
performs steps 1 and 2 itself and refuses on overlap. In worktree teardown,
`migrate-assets.sh` copies state and asset links into the canonical checkout
(`cp -a`), verifies the copy and deletes nothing from the source. Removing the
worktree is a separate step, `issue-workflow` close-out's
`herdr worktree remove`, which runs only under the maintainer's merge approval.
Teardown therefore follows step 5: copy, verify, then delete on a person's
decision.
