# Skills directory rules

Use `shared/` for neutral cross-project procedures and register each shared item
in `.agents/content-registry.yaml`. Other skill directories belong to the
concrete project and must state their commands, evidence and failure boundaries.

Shared skills currently included:

- `shared/worktree-lifecycle/` — reconcile responsibilities before retiring state.
- `shared/issue-workflow/` — scope, dependencies, optional parent integration and delivery.
- `shared/agent-communication/` — capability-based transport and distinct
  submission, acknowledgement and completion receipts.
- `shared/project-memory-governance/`
- `shared/asset-lifecycle/`
- `shared/credential-setup/`
- `shared/cli-first-operations/`
- `shared/long-running-supervision/`
- `shared/template-feedback/`
- `shared/template-adoption/` — positioning and path contracts before migration.
- `shared/template-upgrade/`
- `shared/release-doc-audit/`

Add new skills to this list and to `.agents/content-registry.yaml` in the same
change.

Template skills:

- `template-harvest/` — maintainer-only procedure that collects reusable practice
  adopters have settled; it is not shared content and is never copied downstream.

Register each template skill with `scope: template` in the same change.
