---
name: resolve-real-paths-before-moving
date: 2026-10-19
source: Issue #59, harvested from a downstream adopter of this template; Issue #87 (the checks moved to asset-lifecycle)
scope: shared
applies_to: any move, copy-then-delete, replacement or symlinking of a directory, by an agent or a script
status: active
supersedes: null
superseded_by: null
---

# Resolve real paths before moving a directory

Related: [`llm-credentials.md`](llm-credentials.md) (login directories are never
moved or copied).

## Decision

Before moving a directory, copying it and deleting the source, replacing it, or
turning it into a symlink, prove that source and destination are two different
places holding two different data sets. Deleting a copy is a person's
decision.

## Why

An adopter moved data to another disk while the source path was already a
symlink to the destination. The copy was a no-op. Every check agreed because it
compared the directory with itself, and the following delete removed the only
copy. Free space did not change, which would have shown the problem before the
delete. The same failure appears whenever a path, a parent directory or a
nested entry is a link: renamed checkouts, asset links, mounted volumes.

## Apply

Follow "Before moving, replacing or deleting a directory" in
[`../../skills/shared/asset-lifecycle/SKILL.md`](../../skills/shared/asset-lifecycle/SKILL.md):
its six checks, when each runs, the evidence to report, and how scripts and
worktree teardown follow them.
