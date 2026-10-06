---
name: asset-lifecycle
description: Keep large external assets visible, linked and migratable from a repository.
---

# Asset lifecycle

Use this skill for datasets, model checkpoints, caches or other large assets that
should not be committed to Git.

1. Create a stable repository-visible entry under `assets/`, normally a symlink to
   managed external storage.
2. Register its id, purpose, source, version, checksum and rebuildability in
   `assets/MANIFEST.yaml`.
3. Keep machine-specific targets out of product code. Setup and diagnosis must
   report a missing or broken link clearly.
4. Before retiring a worktree, migrate the manifest, link and any durable records
   using the repository teardown procedure. Check that no unique copy remains in
   the old worktree.
5. Never put credentials, raw auth files or unregistered personal data in the
   asset directory.

The link and manifest are the project control plane; the external storage is only
the payload location.
