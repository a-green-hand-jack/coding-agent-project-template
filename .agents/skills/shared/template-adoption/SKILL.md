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
   Map the optional product release skeleton (`pyproject.toml`, `Dockerfile`,
   `install.sh`, `.dockerignore`) as adopted, adapted, preserved or a local
   conflict; never overwrite an existing product build entrypoint.
   Record the adopted template repository and tag in the registry's `template`
   field; keep the downstream project's own `RELEASE_NOTES.md` separate.
4. Show the map and wait for the user's approval when the repository's local
   rules or public behavior would change. Do not silently overwrite files.
5. On an Issue branch, add or adapt the three planes, `CLAUDE.md -> AGENTS.md`,
   uniform `.agents/**/AGENTS.md` guidance, content registry, worktree setup,
   visible `.project/` state, asset manifest and GitHub templates as applicable.
6. Run the target repository's setup, diagnostics, CLI entrypoints and relevant
   seam checks. Confirm that product payloads do not include `.agents/`, secrets
   or worktree-local state.
7. Report adopted files, adapted files, preserved files, validation evidence and
   unresolved decisions. Leave commit and PR publication to the user's workflow.

The destination repository remains the authority for its product and project
history; this template supplies a development control plane, not a new product.
