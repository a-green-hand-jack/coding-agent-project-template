---
name: llm-credentials
date: 2026-10-15
source: Issue #23, policy decided by the template maintainer
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
2. **Refreshing, non-shareable logins are made once per project, inside the
   project.** This covers the Codex ChatGPT login (`auth.json`), the Claude Code
   interactive login and OAuth logins of other agent CLIs. Each project logs in
   itself, for example `CODEX_HOME=<login dir> codex login --device-auth`, into a
   Git-ignored directory of its own. Never link, copy, snapshot-restore or lend a
   login to another project.
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

## Apply

Each project fills two parameters:

- `SHARED_CREDENTIAL_FILE`: the device's shared file, taken from user-level
  configuration. If the device has none, the project runs without it.
- `CREDENTIAL_DIR`: the Git-ignored project directory that holds the symlink to
  the shared file and the project's own logins.

Then, inside the project:

1. Link `CREDENTIAL_DIR/<name>` to `SHARED_CREDENTIAL_FILE`; reference only the
   link from project code and configuration. `.env.example` names the link or
   the variables, never a value.
2. Log in each refreshing CLI once with its home pointed into `CREDENTIAL_DIR`.
   When a login stops working, log in again; do not restore an older copy.
3. Start sandboxes and subprocesses with the selected variables only.
4. Before writing a tracked file, commit, Issue, PR or log, check that it holds
   no credential value and no path outside the project.

Which directory serves as `CREDENTIAL_DIR` is an open adaptation point. Local
state lives under each worktree's `.project/`, but the worktrees of one project
are one consumer. Two choices:

- **Per canonical checkout:** the logins live in the canonical checkout's
  `.project/`, and each worktree links to them. Concurrent sessions read one
  file, so a refresh is seen by all. Teardown must drop the link and never copy
  the login.
- **Per worktree:** each worktree logs in again in its own `.project/`. There is
  no shared state, but every new worktree needs a new login and the login is
  discarded with the worktree.

Until the maintainer decides, record which choice the project made. Never let a
worktree migration copy a login over the canonical one.
