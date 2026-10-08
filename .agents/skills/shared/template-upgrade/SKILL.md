---
name: template-upgrade
description: Upgrade a downstream repository from one template release to another.
---

# Upgrade a downstream template user

Use this skill when a repository already follows an earlier template release and
needs changes from a newer tag, such as `v0.1.0` to `v0.1.1`.

## Contract

Treat the downstream repository as an owned product. Preserve its product code,
domain docs, local memory, knowledge, skills, assets, public behavior and local
customizations unless the user explicitly approves a change. Never replace the
downstream repository with the template tree or merge template history into it.

## Procedure

1. Identify `template.repository` and `template.version` from the downstream
   registry and record the target release tag, branch, worktree, clean/dirty
   state and current tests.
2. Fetch the target template tag and inspect its release notes and registry. Build
   a path-level migration map from current version to target.
3. Classify each difference as shared addition, required adaptation, local conflict,
   obsolete template behavior or intentionally skipped change. Search local
   Issues, memory and skills before changing an existing rule.
   Treat branch-model and visibility guidance as required shared additions, and
   keep machine-specific asset links out of Git during the migration.
   Migrate legacy memory and knowledge bodies into the new `shared/` and
   `project/` topic files, update their indexes and registry entries, and keep
   unresolved records readable until classification is complete.
   Treat the product release skeleton as optional: preserve an existing package,
   container or installer contract and adapt only the missing pieces, including
   the development-plane exclusions in `.dockerignore`.
   Treat the template repository's `RELEASE_NOTES.md` as template-only content;
   it is not copied into the downstream project's release history.
4. Present the migration map and acceptance plan before mutating a repository when
   conflicts, public behavior or asset paths are involved.
5. Work on an Issue branch. Apply only approved shared changes, adapt commands and
   paths, update `CLAUDE.md` and `.agents/**/AGENTS.md` consistently, and update
   the downstream content registry's `template.version` to the target tag.
6. Run setup, diagnostics, public CLI checks, relevant seam tests and any required
   long-running supervision checks. Verify assets and worktree state remain
   visible and no local product files were overwritten.
7. Report the exact source and target versions, migration decisions, validation
   evidence, skipped changes and remaining risks. Deliver through the downstream
   Issue/PR process.

An upgrade is complete only when the downstream project can explain which template
capabilities it adopted and which it intentionally kept different.
