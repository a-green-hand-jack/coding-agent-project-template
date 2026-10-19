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

1. Identify the template this repository follows from the downstream
   registry (`sed -n '/^template:/,/^[^[:space:]]/p' .agents/content-registry.yaml`):
   `template.upstream` when the block has one (a derived template, whose own
   `template.version` is its own release line and is not changed here),
   otherwise `template.repository` and `template.version`. Below, the template's
   repository and version mean that pair. Record the target release tag,
   branch, worktree, clean/dirty state and current tests. If the registry has
   no `template:` block or no `version:` line (repositories adopted before
   `v0.1.5`), backfill it first as described in "Backfill a missing template
   record"; without it the upgrade has no recorded source version.
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
   the development-plane exclusions in `.dockerignore`. Keep the repository's
   declared product tree (`src/` by default) where template wording names
   `src/`.
   Treat the template repository's `RELEASE_NOTES.md` as template-only content;
   it is not copied into the downstream project's release history.
4. Present the migration map and acceptance plan before mutating a repository when
   conflicts, public behavior or asset paths are involved.
5. Work on an Issue branch. Apply only approved shared changes, adapt commands and
   paths, update `CLAUDE.md` and `.agents/**/AGENTS.md` consistently, and update
   the version of the followed template in the downstream registry to the target
   tag: `template.upstream.version` in a derived template, otherwise
   `template.version` (creating the block if the backfill has not been done
   yet).

   Upgrade each adopted shared skill and memory record by replacing the template
   text above its `## In this repository` section (the whole file when it has
   no section; see `template-adoption` step 5) and keeping the section. With
   `<template>` a clone of the followed template's repository under `.project/`
   holding both tags, `<SOURCE_TAG>` its version currently in the registry and
   `<path>` the file:

   ```bash
   H='## In this repository'
   above() { awk -v h="$H" '$0 == h { exit } /^$/ { b = b "\n"; next } { printf "%s%s\n", b, $0; b = "" }'; }
   section() { awk -v h="$H" '$0 == h { s = 1 } s'; }
   # 1. The text above the section must still be the source release's.
   git -C <template> show <SOURCE_TAG>:<path> | above | diff - <(above < <path>)
   # 2. Replace it with the target release's and keep the section.
   { git -C <template> show <TARGET_TAG>:<path> | above
     [ -z "$(section < <path>)" ] || { echo; section < <path>; }
   } > <path>.new && mv <path>.new <path>
   ```

   - Check 1 must print nothing. A difference is a local edit above the section
     and therefore a local conflict: move it into the section as an addition
     keyed to its step, or drop it when the target release covers it, then
     rerun the check. A repository adopted before this convention does this
     once, at its first upgrade after it.
   - Reconcile only the section. Read
     `git -C <template> diff <SOURCE_TAG> <TARGET_TAG> -- <path>` for new,
     renamed or removed slots and for steps that moved or changed, and update the
     slot rows and the step keys of the additions. When the followed template
     is a derived template, that diff also shows changes to its own section,
     which this repository's section continues; carry them over in the same
     way.

   Replace adopted scripts whole; the project's
   `.agents/scripts/setup-project.sh` and `.agents/scripts/migrate-project.rules`
   are not template files and stay. A local edit to an adopted script is a local
   conflict: move it into one of those two files (`template-adoption` step 5), or
   report it through `template-feedback` when neither can hold it. When the
   target `migrate-assets.sh` handles an entry itself, it refuses the project's
   rule for that entry; remove the line.
6. Run setup, diagnostics, public CLI checks, relevant seam tests and any required
   long-running supervision checks. Verify assets and worktree state remain
   visible and no local product files were overwritten.
7. Report the exact source and target versions, migration decisions, validation
   evidence, skipped changes and remaining risks. Deliver through the downstream
   Issue/PR process.

An upgrade is complete only when the downstream project can explain which template
capabilities it adopted and which it intentionally kept different.

## Backfill a missing template record

A repository adopted before `v0.1.5` records its adopted release only in its
developer docs or git history, and `.agents/scripts/diagnose-environment.sh`
reports a missing registry `template.version`. On the Issue branch, before the
migration map:

1. Read the adopted tag from the evidence:

   ```bash
   grep -nE 'v[0-9]+\.[0-9]+\.[0-9]+' DEV.md
   git log --reverse --format='%h %s' -- .agents/content-registry.yaml
   ```

   The developer docs or the adoption commit normally name the tag. If they
   disagree or neither names one, do not guess: compare the repository's
   template-derived files with the candidate release tags, or ask the maintainer.
   Record which evidence the tag came from.
2. Insert the block, replacing `<TAG>` with the adopted tag. The command adds it
   before the first top-level key that follows `purpose:`. If a `template:` key
   already exists without `version:`, add the `version:` line by hand instead:

   ```bash
   awk -v tag=<TAG> '/^(default_scope|matching|classes|entries):/ && !done { print "template:"; print "  repository: https://github.com/a-green-hand-jack/coding-agent-project-template"; print "  version: " tag; done = 1 } { print }' .agents/content-registry.yaml > .agents/content-registry.yaml.new && mv .agents/content-registry.yaml.new .agents/content-registry.yaml
   ```

3. Verify with `grep -A2 '^template:' .agents/content-registry.yaml`, and with
   `bash .agents/scripts/diagnose-environment.sh` once the target scripts are
   in place.

The backfilled value is the release the repository **adopted**. Step 5 of the
procedure later moves it to the target tag; list the backfill in the migration
report with its evidence.
