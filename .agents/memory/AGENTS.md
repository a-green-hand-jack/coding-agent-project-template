# Memory rules and index

Memory records durable decisions, principles and lessons. Keep session notes,
temporary run paths and private context out of this directory. Use one topic per
file under `shared/` or `project/`; do not append entries to this index.

- [`shared/`](shared/AGENTS.md) — reusable decisions that may be synchronized
  across projects after adaptation.
- [`project/`](project/AGENTS.md) — decisions owned by this repository.
- [`entry-template.md`](entry-template.md) — front matter and body structure for
  a new record.

Search the relevant index before creating a record. Register the entry in
`content-registry.yaml`, then generate group index blocks with
`bash .agents/scripts/shared/check-development.sh --write-indexes`. Maintain
only the static group navigation above by hand.
