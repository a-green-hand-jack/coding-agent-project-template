# Shared memory rules and index

This directory contains durable decisions that are neutral enough to reuse
across projects. Every record is a separate Markdown file with the fields in
[`../ENTRY_TEMPLATE.md`](../ENTRY_TEMPLATE.md), `scope: shared`, and an active
or superseded status.

## Index

- [`issue-in-herdr-worktree.md`](issue-in-herdr-worktree.md) — implement each
  Issue in its own Herdr worktree and agent session.
- [`issue-close-out.md`](issue-close-out.md) — close out an Issue's worktree
  automatically after its PR merges.
