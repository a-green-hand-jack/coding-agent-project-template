# Shared memory rules and index

This directory contains durable decisions that are neutral enough to reuse
across projects. Every record is a separate Markdown file with the fields in
[`../ENTRY_TEMPLATE.md`](../ENTRY_TEMPLATE.md), `scope: shared`, and an active
or superseded status. A record that names parameters for the destination is
registered `shared_with_adaptation`; the destination writes their values in a
trailing `## In this repository` section (see `template-adoption` step 5), and
the record's own text never contains that heading line.

## Index

- [`issue-in-herdr-worktree.md`](issue-in-herdr-worktree.md) — implement each
  Issue in its own Herdr worktree and agent session, which verifies to
  completion, fixes related defects and leaves conflicts to the dev checkout.
- [`issue-close-out.md`](issue-close-out.md) — close out an Issue's worktree
  right after its PR merges; the merge approval covers the close-out, and live
  runs in the dev checkout or containers mounting the worktree stop it.
- [`issue-dispatch-by-difficulty.md`](issue-dispatch-by-difficulty.md) — dispatch
  each Issue agent with an explicit model and effort for its difficulty tier, and
  record it in the Issue.
- [`llm-credentials.md`](llm-credentials.md) — share stable LLM credentials
  through one device file; log refreshing logins in once per canonical checkout,
  whose worktrees link to them.
- [`product-state-root.md`](product-state-root.md) — product commands resolve
  the worktree's state root from an argument, an environment variable, the
  nearest setup marker (stopping at the repository boundary), then a default.
- [`run-settings-from-config.md`](run-settings-from-config.md) — run parameters
  are settings loaded from configuration with a fixed override order, recorded
  at run start and reused on resume; never constants in code.
- [`third-party-llm-compat-patches.md`](third-party-llm-compat-patches.md) —
  compatibility changes to third-party LLM tools live in the repository and run
  every time; check one captured request body before a batch; no retry-without-
  the-parameter fallbacks.
