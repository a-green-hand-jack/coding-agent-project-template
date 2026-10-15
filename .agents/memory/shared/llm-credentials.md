---
name: llm-credentials
date: 2026-10-15
source: Issue #23 (policy); Issue #27 (per-canonical-checkout decision by the template maintainer)
scope: shared
applies_to: repositories whose code, tools or agents call LLM providers with API keys, tokens or OAuth logins
status: active
supersedes: null
superseded_by: null
---

# Manage LLM credentials across projects

## Decision

1. **Stable, reusable credentials live in one shared file per device.** API keys
   and non-refreshing tokens (for example a `CLAUDE_CODE_OAUTH_TOKEN` from
   `claude setup-token`) that several consumers can use concurrently without
   interfering. Keep one file, mode 0600 inside a 0700 directory, and no copies.
   Its location is a device-level parameter supplied by user-level
   configuration, not by the template; a device may hold none.
2. **Refreshing, non-shareable logins are made once per project, in the
   canonical checkout's `.project/`.** This covers the Codex ChatGPT login
   (`auth.json`), the Claude Code interactive login and OAuth logins of other
   agent CLIs. Each project logs in itself, for example
   `CODEX_HOME=<login dir> codex login --device-auth`, into a Git-ignored
   directory `CREDENTIAL_DIR` under the canonical checkout's `.project/`. The
   project's worktrees link to that directory and never log in again. Never
   link, copy, snapshot-restore or lend a login to another project.
3. **The project stays self-contained.** Code, configuration and documentation
   reference only paths inside the project. The shared file is reached through a
   symlink in a Git-ignored project directory. Credential values never enter Git,
   logs, Issues or PRs.
4. **Hand over only what is needed.** When passing credentials to a sandbox or
   subprocess, the project selects the variables that process needs and never
   passes the whole shared file.

## Why

Projects that each invented their own handling kept logins outside the
repository, copied API keys into per-project `.env` files or linked one
project's login from another. Two failures followed. Two consumers sharing one
refreshing login invalidate each other once both refresh, because a refresh
token such as Codex's is single-use. Restoring an older snapshot of a refreshing
login over a newer one silently overwrites the refreshed token. Stable keys do
not have this problem, so one guarded copy per device is enough for them.

The worktrees of one project are one consumer. Each reads the same login through
its link, so a refresh made in one session is seen by all of them. A login per
worktree would need a new login for every worktree and would be lost with it.

## Apply

Each project fills two parameters:

- `SHARED_CREDENTIAL_FILE`: the device's shared file, taken from user-level
  configuration. If the device has none, the project runs without it.
- `CREDENTIAL_DIR`: the name of the Git-ignored directory under the canonical
  checkout's `.project/` that holds the symlink to the shared file and the
  project's own logins.

Then, in the canonical checkout:

1. Link `CREDENTIAL_DIR/<name>` to `SHARED_CREDENTIAL_FILE`; reference only the
   link from project code and configuration. `.env.example` names the link or
   the variables, never a value.
2. Log in each refreshing CLI once with its home pointed into `CREDENTIAL_DIR`.
   When a login stops working, log in again in the canonical checkout; do not
   restore an older copy.
3. Start sandboxes and subprocesses with the selected variables only.
4. Before writing a tracked file, commit, Issue, PR or log, check that it holds
   no credential value and no path outside the project.

In each worktree of the project, the same `CREDENTIAL_DIR` is a link to the
canonical checkout's directory. A worktree never holds a login of its own, never
logs in, and never restores a login from a snapshot. Teardown and migration of a
worktree drop that link and never copy a login, in particular never over the
canonical one.
