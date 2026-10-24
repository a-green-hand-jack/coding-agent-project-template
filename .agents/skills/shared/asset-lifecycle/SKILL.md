---
name: asset-lifecycle
description: Keep large external assets visible, linked and migratable from a repository, and prove source and destination differ before moving, replacing or deleting any directory.
---

# Asset lifecycle

Use this skill for datasets, model checkpoints, caches or other large assets that
should not be committed to Git, and before any move, copy-then-delete,
replacement or symlinking of a directory, by an agent or a script (last section).

1. Create a stable repository-visible entry under `assets/`, normally a symlink to
   managed external storage.
2. Register its id, purpose, source, version, checksum and rebuildability in
   `assets/MANIFEST.yaml`.
3. Keep machine-specific targets out of product code. Setup and diagnosis must
   report a missing or broken link clearly.
4. Before retiring a worktree, migrate the manifest, link and any durable records
   using the repository teardown procedure. Check that no unique copy remains in
   the old worktree.
   Before moving, replacing or re-linking an asset's storage, or deleting a copy,
   follow [Before moving, replacing or deleting a directory](#before-moving-replacing-or-deleting-a-directory):
   a link can make source and destination the same directory.
5. Never put credentials, raw auth files or unregistered personal data in the
   asset directory.

The link and manifest are the project control plane; the external storage is only
the payload location.

## Before moving, replacing or deleting a directory

Before moving a directory, copying it and deleting the source, replacing it, or
turning it into a symlink, prove that source and destination are two different
places holding two different data sets
([`resolve-real-paths-before-moving`](../../../memory/shared/resolve-real-paths-before-moving.md)
records why). Run steps 1 and 2 before the first write, step 3 after the copy,
and steps 4 to 6 before any delete.

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

Report the resolved paths, the device and inode pair and the space figures with
the result. A script that moves or replaces directories performs steps 1 and 2
itself and refuses on overlap. In worktree teardown, `migrate-assets.sh` copies
state and asset links into the canonical checkout (`cp -a`), verifies the copy
and deletes nothing from the source. Removing the worktree is a separate step,
`issue-workflow` close-out's `herdr worktree remove`, which runs only under the
maintainer's merge approval. Teardown therefore follows step 5: copy, verify,
then delete on a person's decision.
