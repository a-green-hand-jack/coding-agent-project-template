# Skills directory rules

Use `shared/` for neutral cross-project procedures and register each shared item
in `.agents/content-registry.yaml`. Other skill directories belong to the
concrete project and must state their commands, evidence and failure boundaries.

Shared skills currently included:

- `shared/worktree-lifecycle/` — reconcile responsibilities before retiring state.
- `shared/issue-workflow/` — scope, dependencies, delivery events, acceptance
  write responsibility, Codex caller identity/isolation and coordinator reconciliation.
- `shared/development-writing/` — reader decisions, current facts and evidence
  for Issues, PRs, comments and commits; four neutral cases in references.
- `shared/agent-communication/` — capability-based transport and distinct
  submission, acknowledgement and completion receipts, message cadence,
  pending recovery and receive-time backlog/terminal reconciliation;
  acceptance/cadence scenario review in references.
- `shared/project-memory-governance/`
- `shared/asset-lifecycle/`
- `shared/credential-setup/`
- `shared/cli-first-operations/`
- `shared/long-running-supervision/`
- `shared/template-feedback/`
- `shared/template-adoption/` — positioning and path contracts before migration.
- `shared/template-upgrade/`
- `shared/release-doc-audit/` — self-contained release narratives, visual review
  and version/registry/upgrade consistency; release-type guidance in references.

Add new skills to this list and to `.agents/content-registry.yaml` in the same
change.

Template skills:

- `template-harvest/` — maintainer-only procedure that collects reusable practice
  adopters have settled; it is not shared content and is never copied downstream.

Register each template skill with `scope: template` in the same change.
