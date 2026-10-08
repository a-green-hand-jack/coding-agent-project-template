# Skills directory rules

Use `shared/` for neutral cross-project procedures and register each shared item
in `.agents/content-registry.yaml`. Other skill directories belong to the
concrete project and must state their commands, evidence and failure boundaries.

Shared skills currently included:

- `shared/worktree-lifecycle/`
- `shared/project-memory-governance/`
- `shared/asset-lifecycle/`
- `shared/cli-first-operations/`
- `shared/long-running-supervision/`
- `shared/template-feedback/`
- `shared/template-adoption/`
- `shared/template-upgrade/`
- `shared/release-doc-audit/`

Add new skills to this list and to `.agents/content-registry.yaml` in the same
change.
