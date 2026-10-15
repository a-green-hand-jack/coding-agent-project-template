---
name: product-state-root
date: 2026-10-15
source: Issue #42, harvested from a downstream adopter of this template
scope: shared
applies_to: repositories whose product commands keep persistent state per worktree under the worktree's `.project/`
status: active
supersedes: null
superseded_by: null
---

# Product commands find the worktree's state root from the setup marker

## Decision

1. **The product CLI resolves its state root in a fixed order:**
   1. an explicit argument;
   2. an environment variable (`STATE_ENV`);
   3. the nearest setup marker (`STATE_MARKER`), found by walking up from the
      current directory without crossing the repository boundary, a directory
      that contains `.git`;
   4. a user-level default (`DEFAULT_ROOT`).
2. **The marker holds one absolute path and no credentials, and Git ignores it.**
   `setup-worktree.sh` writes `.project/home`; a product may write its own marker
   from `setup-project.sh`.
3. **Teardown migrates the state the marker points to** (see
   [`issue-close-out.md`](issue-close-out.md)).

## Why

The template says that all local state of a worktree goes into that worktree's
`.project/`, but not how the product's own commands find it. Coding agents run
commands from tool subprocesses that do not reliably inherit a shell
environment: a variable exported in one command is gone in the next. A product
that relies on the variable, or falls back to a user-level default, writes a
worktree's runs into a shared location or into another worktree's state, and
removing or migrating the worktree then misses them. Stopping the walk at the
repository boundary keeps a nested checkout from inheriting a parent's marker.
One downstream adopter has resolved its state root this way since it introduced
per-worktree state; every command started in a worktree, including agents'
subprocesses, lands in that worktree's state.

## Apply

Each project fills three parameters:

- `STATE_MARKER`: the marker path relative to a worktree root, for example
  `.project/home`, or a product-specific marker written by `setup-project.sh`.
- `STATE_ENV`: the name of the environment variable that overrides the marker.
- `DEFAULT_ROOT`: the user-level default used outside any worktree.

Then:

1. Implement the order above in one resolver in the product code, and have every
   command that reads or writes state call it. The template ships no resolver.
2. Make setup write `STATE_MARKER` with the worktree's absolute path, and keep
   the marker ignored by Git.
3. Stop the upward walk at the first directory that contains `.git`; if that
   directory has no marker, continue with `DEFAULT_ROOT`.
4. Check a command started from a subdirectory of a worktree, with a fresh
   environment and `STATE_ENV` unset, writes under that worktree's state root.

A product without persistent state does not need this record.
