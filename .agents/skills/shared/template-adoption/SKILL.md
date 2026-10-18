---
name: template-adoption
description: Adapt an existing repository to this coding-agent project template.
---

# Adopt the template in an existing repository

Use this skill when a repository already has product code, history, users and
development practices, and should gain this template's project control plane.

## Contract

Preserve the existing product, public behavior, history, credentials boundary and
working assets. This is a migration, not a replacement with a fresh template
copy. Do not copy the template's issue history, `.project/` state, release notes,
example assets or project-specific memory and knowledge.

## Procedure

1. Record the target repository, current branch, clean/dirty state, remotes,
   default entrypoints, runtime state locations and asset locations.
2. Read the target repository's agent instructions and contributor docs. Compare
   them with the template release requested by the user (for example `v0.1.1`).
3. Produce a migration map before editing:
   - adopt unchanged: neutral rules and shared skills;
   - adapt: paths, commands, product docs, environment and evidence;
   - preserve: existing product code, domain docs, tests and project memory;
   - reject: content that would duplicate or hide an existing source of truth.
   Include repository visibility and the `dev`/`main` branch model in the map;
   confirm the target visibility before writing public Issues, PRs or releases.
   Map legacy `memory/AGENTS.md` and `knowledge/AGENTS.md` records into one
   topic per file under `shared/` or `project/`, preserving the old text until
   each record has a destination and front matter.
   If the repository calls LLM providers, from its own code, agent CLIs or
   third-party tools it runs, map the shared `llm-credentials` and
   `third-party-llm-compat-patches` memory records and the
   `gpt5-strict-backend-requests` knowledge record together: adapt the
   credential parameters, locate any local edits to third-party tools and move
   them into the repository as patches, and keep the knowledge record's date and
   refresh condition. Skip them when the project calls no LLM.
   Map the optional product release skeleton (`pyproject.toml`, `Dockerfile`,
   `install.sh`, `.dockerignore`) as adopted, adapted, preserved or a local
   conflict; never overwrite an existing product build entrypoint.
   Record the adopted template repository and tag in the registry's `template`
   field; keep the downstream project's own `RELEASE_NOTES.md` separate.
   If the repository already carries an earlier adoption whose registry has no
   `template:` block, read the adopted tag from its developer docs or git history
   and backfill the block first, following `template-upgrade`
   ("Backfill a missing template record").
4. Show the map and wait for the user's approval when the repository's local
   rules or public behavior would change. Do not silently overwrite files.
5. On an Issue branch, add or adapt the three planes, `CLAUDE.md -> AGENTS.md`,
   uniform `.agents/**/AGENTS.md` guidance, content registry, worktree setup,
   visible `.project/` state, asset manifest and GitHub templates as applicable.
   Merge the template's `.gitignore` entries into the existing `.gitignore`
   rather than replacing it: `.project/`; `assets/*` with the exceptions
   `!assets/README.md`, `!assets/MANIFEST.yaml` and `!assets/.gitkeep`; and
   `!.env.example` after any `.env.*` rule. A rule already in the repository
   (`.env.*`, `assets/`) can hide `.env.example` or `assets/MANIFEST.yaml`, so
   they exist locally but never reach a commit or CI;
   `diagnose-environment.sh` fails with the fix when that happens.
   If the product resolves a state root of its own, follow the shared
   `product-state-root` memory record next to the setup hook
   (`.agents/scripts/setup-project.sh`) so every command started in a worktree
   finds that worktree's `.project/`.

   Copy shared skills and memory records registered `shared_with_adaptation`
   verbatim and adapt them only in one trailing section, so that
   `template-upgrade` can replace the template text without conflicts:
   - End the file with the heading `## In this repository`. Everything from that
     heading to the end of the file belongs to this repository; the text above
     it is the template's and is never edited.
   - Write slot values as a table with the columns Slot and Value, one row per
     slot the file defines (for example the `issue-workflow` adaptation slots).
     A slot left out takes its default. A value that does not fit a table cell
     (a pattern or command containing `|`) is written as a code block under the
     section, naming its slot.
   - Write every other adaptation as an addition keyed to the step it extends,
     naming the step and its first words so that a renumbered step is noticed
     at upgrade, for example "Start step 4 (Start the agent): also pass ...".
     A local rule that has to replace a template step is keyed the same way,
     says "instead", and is reported through `template-feedback`.
   - When nothing needs adapting, the section says so in one line.

   Adopt scripts unchanged and put project-specific setup in the
   `.agents/scripts/setup-project.sh` hook. When that hook creates entries in
   `.project/`, say in `.agents/scripts/migrate-project.rules` how teardown
   migrates each one, one `NAME|ACTION|WHY` line per entry: `copy`, `drop` with
   the reason it may be left behind, or `login` for a link to the canonical
   checkout's login directory (`llm-credentials`; the link is dropped and a real
   copy blocks). The template ships neither file, so `template-upgrade` keeps
   both. Rewrite the other
   `shared_with_adaptation` files (`AGENTS.md`, the registry, product skeletons)
   for the repository.
6. Run the target repository's setup, diagnostics, CLI entrypoints and relevant
   seam checks. Confirm that product payloads do not include `.agents/`, secrets
   or worktree-local state.
7. Report adopted files, adapted files, preserved files, validation evidence and
   unresolved decisions. Leave commit and PR publication to the user's workflow.

The destination repository remains the authority for its product and project
history; this template supplies a development control plane, not a new product.
