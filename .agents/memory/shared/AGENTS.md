# Shared memory rules and index

This directory contains durable decisions that are neutral enough to reuse
across projects. Every record is a separate Markdown file with the fields in
[`../ENTRY_TEMPLATE.md`](../ENTRY_TEMPLATE.md), `scope: shared`, and an active
or superseded status.

## Index

- [`issue-in-herdr-worktree.md`](issue-in-herdr-worktree.md) — implement each
  Issue in its own Herdr worktree and agent session, which verifies to
  completion, fixes related defects and leaves conflicts to the dev checkout.
- [`issue-close-out.md`](issue-close-out.md) — close out an Issue's worktree
  right after its PR merges; the merge approval covers the close-out.
- [`issue-dispatch-by-difficulty.md`](issue-dispatch-by-difficulty.md) — dispatch
  each Issue agent with an explicit model and effort for its difficulty tier, and
  record it in the Issue.
- [`llm-credentials.md`](llm-credentials.md) — share stable LLM credentials
  through one device file; log refreshing logins in once per canonical checkout,
  whose worktrees link to them.
