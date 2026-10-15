# Release notes

## v0.1.9 — 2026-10-15

- Shared skills and memory records registered `shared_with_adaptation` keep the template text verbatim; each adopter writes its slot values and step-keyed additions in one trailing `## In this repository` section, so `template-upgrade` replaces the text above it without conflicts. `template-adoption`, `template-upgrade`, the registry rule and `issue-workflow` state the convention, and `diagnose-environment.sh` warns when a downstream file lacks the section.
- `issue-workflow` checks the dev checkout for a live run before every pull or merge, and close-out stops on any container (running or stopped) that mounts the worktree: `inspect-state.sh` lists them and exits 3. `long-running-supervision` forbids editing code under a live run in place.
- `issue-workflow` Start labels the Issue workspace `<WORKSPACE_PREFIX>-issue-<N>`.
- `diagnose-environment.sh` fails, with the fix, when `.env.example` or `assets/MANIFEST.yaml` is ignored by Git or `.project/` is not; `template-adoption` names the `.gitignore` entries to merge.
- `template-feedback` asks for the kind of downstream instead of naming a private repository.
- `release-doc-audit` is `shared_with_adaptation`, with a `RELEASE_HEADING` parameter for the release-notes layout.
- Added the shared `product-state-root` memory record (state root from the setup marker), the shared `third-party-llm-compat-patches` memory record and the first shared knowledge record, `gpt5-strict-backend-requests`, linked from `llm-credentials` and `template-adoption`.
- Recorded the pre-release downstream harvest in project memory.

## v0.1.8 — 2026-10-15

- Added the shared `llm-credentials` memory record: stable keys in one device-level shared file reached through a project-local link, refreshing logins once per project in the canonical checkout's `.project/credentials`, only selected variables passed to children, and safe re-login (never through a link, keep the failed login, the maintainer logs in). `setup-worktree.sh` links a worktree's `.project/credentials` to the canonical checkout; `migrate-assets.sh` drops that link and blocks on a real login copy.
- Added dispatch by difficulty to `issue-workflow`: four tiers with explicit model and effort slots, a Dispatch section in the Issue body, and a fallback agent only when the primary is unavailable; recorded in the shared `issue-dispatch-by-difficulty` memory.
- Issue handoffs now carry four working rules (`new-agent-prompt.sh`, `issue-workflow`): verify to completion and report one definite result, fix related defects met on the way, leave conflicts between worktrees to the dev checkout, and merge approval covers the close-out. `DEV.md` and the PR template no longer ask for a "not verified" list.
- Added the shared `run-settings-from-config` memory record: run parameters are settings with a fixed override order, recorded at run start and reused on resume.
- Removed the empty top-level `tests/` directory and its references.
- Recorded the 2026-10-15 downstream harvest in project memory.

## v0.1.7 — 2026-10-13

- Added the shared `issue-workflow` skill covering Herdr start, merge and close-out, with adaptation slots for agent, repository, CI and product commands.
- Added shared memory records for implementing each Issue in its own Herdr worktree and closing it out after merge, and populated the shared memory index.
- Added a "Backfill a missing template record" step to `template-upgrade` and `template-adoption`, and made `diagnose-environment.sh` explain how to backfill a missing registry `template` block instead of failing without a reason.
- Added the maintainer-only `template-harvest` skill (`scope: template`) and wired it into the release checklist: it discovers adopters from the registry marker, inventories what they settled, and brings reusable practice back through the normal Issue process.
- `setup-worktree.sh` now gives a new worktree the primary checkout's asset-link mappings and hand-made `assets/` links, with the worktree's own mapping first; `diagnose-environment.sh` checks both link files.
- `migrate-assets.sh` now names every `.project/` entry with its action, size and reason; stops on an unknown entry that holds something until `--also`/`--skip` decides it; merges asset-link mappings into the destination; and verifies the copy afterwards, writing a `migration-report.txt`. `teardown-worktree.sh` passes `--also`/`--skip` through.
- `DEV.md` documents the template relationship: which tag a project follows, upgrade through `template-upgrade`, feedback through `template-feedback`, and its own release notes.
- Release documentation audit fixes: `README.md` and `USER.md` no longer pin a stale example tag (they use a `<TEMPLATE_TAG>` placeholder), and `release-doc-audit` names the release being prepared in its `TARGET_TAG` example.

## v0.1.6 — 2026-10-08

- Fixed release-doc-audit version scanning to include hidden development-plane files.

## v0.1.5 — 2026-10-08

- Added the shared `release-doc-audit` skill for pre-release documentation checks.
- Recorded the adopted template repository and version in the content registry.
- Classified template release notes and separated them from downstream release history.

## v0.1.4 — 2026-10-07

- Added optional package, container and installer skeletons for product releases.
- Added `.dockerignore` boundaries and diagnostics to keep development files out of products.
- Documented adoption and upgrade handling for existing build and install contracts.

## v0.1.3 — 2026-10-07

- Structured memory and knowledge into shared/project topic directories.
- Added front matter templates and rules-only indexes.
- Updated governance, adoption and upgrade guidance for legacy single-file records.

## v0.1.2 — 2026-10-07

- Added idempotent `dev`/`main` branch initialization and diagnostics.
- Documented Herdr worktree and new-pane agent handoff for Issue work.
- Kept machine-specific asset links out of Git and fixed tracked-asset migration.
- Added repository visibility guidance and checks for public writes and template feedback.

## v0.1.1 — 2026-10-06

- Added `template-adoption` for migrating existing repositories into the template.
- Added `template-upgrade` for controlled downstream upgrades between releases.
- Added copy-ready user prompts for both operations.

## v0.1.0 — 2026-10-06

- Initial three-plane coding-agent project skeleton.
- Visible worktree state, setup, diagnostics, asset migration and teardown.
- Claude Code discovery through `CLAUDE.md -> AGENTS.md`.
- Shared skills for worktrees, memory governance, assets, CLI operations,
  long-running supervision and downstream template feedback.
- GitHub Issue/PR templates and template structure checks.
