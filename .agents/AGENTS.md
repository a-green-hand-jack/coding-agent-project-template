# Development plane rules

This directory belongs to coding agent development. It never belongs in the
product runtime or release payload.

Read `.agents/content-registry.yaml` before adding or reusing a memory,
knowledge entry, skill or script. Keep the registry and its index files updated
in the same change as the content decision.

## Directory guidance convention

Every managed subdirectory directly under `.agents/` has an `AGENTS.md` with
its local rules. Grouping directories such as `skills/shared/` also have one.
Individual skill packages use `SKILL.md` as their entry point and do not add a
duplicate `AGENTS.md`. Keep this convention uniform when adding directories.

## Where information goes

- A durable decision, correction or project lesson goes in `memory/` and its
  index before it counts as recorded.
- A changing environment or external fact goes in `knowledge/`, with date and
  source.
- A repeatable operation goes in `skills/`.
- Product behavior belongs in the root product, user or developer documents,
  not here.
- Session progress may remain private; project knowledge may not.

Never store credentials, raw authentication files, private sessions or personal
data here.
