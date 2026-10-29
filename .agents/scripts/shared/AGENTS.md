# Scripts shared rules

Follow the category rules and the content registry.
Shared may be empty; do not generalize project implementations just to fill it.

<!-- registry-index:start -->
- [check-development.sh](check-development.sh) — Public development-plane registry and layout check.
- [check-shells.sh](check-shells.sh) — Check every nested development Shell script without missing glob arguments.
- [content_registry.py](content_registry.py) — Validate development identities, naming, provenance, lifecycle and generated indexes.
- [diagnose-environment.sh](diagnose-environment.sh) — Check environment, branch model, adaptation sections and asset visibility.
- [init-branches.sh](init-branches.sh) — Initialize the declared dev/main branch model.
- [inspect-state.sh](inspect-state.sh) — Inspect local state and containers mounting this worktree.
- [migrate-assets.sh](migrate-assets.sh) — Migrate and verify owned state and asset links before worktree retirement.
- [new-agent-prompt.sh](new-agent-prompt.sh) — Generate a scoped Issue handoff from the current registry and workflow.
- [probe-credentials.sh](probe-credentials.sh) — Report only the status of explicitly declared credential requirements.
- [setup-worktree.sh](setup-worktree.sh) — Initialize worktree-local state, asset links and project setup.
- [teardown-worktree.sh](teardown-worktree.sh) — Check retirement preconditions and migrate local state.
- [upgrade-template.sh](upgrade-template.sh) — Apply reviewed template upgrades with schema and identity-aware path migration.
<!-- registry-index:end -->
