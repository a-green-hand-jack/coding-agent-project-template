---
name: project-memory-governance
description: Classify, register, update and clean shared project development knowledge.
---

# Project memory governance

Use this skill after a user decision, a correction, a repeatable procedure or a
fact that future sessions would otherwise need to rediscover.

1. Search the relevant `memory/` or `knowledge/` index and its `shared/` and
   `project/` directories for an existing entry. `AGENTS.md` files are rules and
   indexes only; never append record text to them.
2. Classify the information:
   - **memory**: a durable decision, principle or lesson and its reason;
   - **knowledge**: a dated fact that may change and its source;
   - **skill**: a repeatable procedure with commands, evidence and failure limits.
3. Check the content registry and choose exactly one destination: `shared/` for
   reusable content or `project/` for repository-owned content. Mark the entry
   `shared` only if it does not depend on a product name, repository path,
   machine, provider, benchmark or private decision. Otherwise keep it project-specific.
4. Create one focused Markdown file from `memory/ENTRY_TEMPLATE.md` or
   `knowledge/ENTRY_TEMPLATE.md`. Fill in front matter for `name`, `date`,
   `source`, `scope`, `applies_to`, `status` and the relevant supersession or
   refresh field.
5. Add one short link and summary to the matching `shared/AGENTS.md` or
   `project/AGENTS.md`, and update `content-registry.yaml` when the path is a
   reusable entry. Do not duplicate the full record in an index.
6. When cleaning up, find inbound links and competing rules first. Mark an old
   entry `status: superseded` and link its replacement; remove it only when its
   history is already preserved by Git and no current link depends on it.
7. Review the resulting diff for secrets, private paths and duplicated rules.

## Migrating legacy single-file records

For a downstream repository whose `memory/AGENTS.md` or `knowledge/AGENTS.md`
contains dated records, preserve the original text in Git history, split each
topic into a file under `shared/` or `project/`, add the required front matter,
and replace the old body with rules plus a short index. Classify each record
independently; do not infer `shared` merely because the old file was copied
from this template.

Private agent memory can hold session progress, but it never counts as project
memory until the repository entry exists.
