---
name: llm-credentials
date: 2026-10-15
source: Issue #23 (policy); Issue #27 (per-canonical-checkout decision by the template maintainer); Issue #31 (safe re-login)
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

Each project fills two parameters in the `## In this repository` section at the
end of this record (see `template-adoption` step 5):

- `SHARED_CREDENTIAL_FILE`: the device's shared file, taken from user-level
  configuration. If the device has none, the project runs without it.
- `CREDENTIAL_DIR`: the name of the Git-ignored directory under the canonical
  checkout's `.project/` that holds the symlink to the shared file and the
  project's own logins. This project uses `credentials`.

Then, in the canonical checkout:

1. Link `CREDENTIAL_DIR/<name>` to `SHARED_CREDENTIAL_FILE`; reference only the
   link from project code and configuration. `.env.example` names the link or
   the variables, never a value.
2. Log in each refreshing CLI once with its home pointed into `CREDENTIAL_DIR`.
   When a login stops working, log in again in the canonical checkout; do not
   restore an older copy.
3. Before logging in again, check that the login file in the credential home (for
   example `auth.json`) is a regular file and not a symlink. If it is a link,
   stop and report; do not log in through it, because the CLI may write the new
   login into the file the link points to, which another consumer owns. Rename
   the failed login in place (for example to `auth.json.failed`) instead of
   deleting or overwriting it, so the evidence of what went wrong is kept.
   Agents never create, edit, copy or restore login files. They report the
   failure and the exact login command, and the maintainer logs in interactively.
   This check rests on the CLI writing through a link. A CLI that replaces a link
   atomically (writes a new file and renames it over the path) would instead
   swap the link for a regular file and leave the target untouched; if a login
   shows that, the premise is wrong for that CLI and this point needs revising.
4. Start sandboxes and subprocesses with the selected variables only.
5. Before writing a tracked file, commit, Issue, PR or log, check that it holds
   no credential value and no path outside the project.

In each worktree of the project, the same `CREDENTIAL_DIR` is a link to the
canonical checkout's directory. `setup-worktree.sh` creates that link when the
canonical checkout has the directory. A worktree never holds a login of its own,
never logs in, and never restores a login from a snapshot. `migrate-assets.sh`
(used by worktree teardown) drops the link and never copies a login; a real copy
of a login inside a worktree blocks the migration until someone checks it by hand.
