# Knowledge rules and index

Knowledge records dated, sourced facts that may change. Keep entries
project-specific unless `.agents/content-registry.yaml` marks a neutral entry as
shared. Never store secrets or raw environment files. Use one topic per file
under `shared/` or `project/`; do not append facts to this index.

- [`shared/`](shared/AGENTS.md) — reusable facts whose source and refresh rule
  apply across projects.
- [`project/`](project/AGENTS.md) — facts owned by this repository.
- [`ENTRY_TEMPLATE.md`](ENTRY_TEMPLATE.md) — front matter and body structure for
  a new record.

Search the relevant index before creating a record. Update the index link and
`content-registry.yaml` in the same change when adding a reusable entry.
