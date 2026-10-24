---
name: credential-setup
description: Set up a project's LLM credentials under the llm-credentials decisions — link the device's shared file, log each refreshing CLI in once in the canonical checkout, re-login without losing the failed login, hand credentials over by name, and keep values out of every output.
---

# Credential setup

Use this skill when a project's code, tools or agents call LLM providers with
API keys, tokens or OAuth logins: when a project adopts it, when a login stops
working, and when a sandbox or subprocess needs credentials. The decisions and
their reasons are in
[`llm-credentials`](../../../memory/shared/llm-credentials.md); the formats of
`inventory.yaml` and `credentials.yaml` and what `probe-credentials.sh` checks
and prints are in
[`credential-inventory`](../../../knowledge/shared/credential-inventory.md).

The steps use that record's two parameters, `SHARED_CREDENTIAL_FILE` and
`CREDENTIAL_DIR`. The project fills them, and writes its own additions to a step
below, in the trailing `## In this repository` section of `llm-credentials`.

## In the canonical checkout

1. Link `CREDENTIAL_DIR/<name>` to `SHARED_CREDENTIAL_FILE`; reference only the
   link from project code and configuration. `.env.example` names the link or
   the variables, never a value.
2. Log in each refreshing CLI once with its home pointed into `CREDENTIAL_DIR`,
   for example `CODEX_HOME=<login dir> codex login --device-auth`. When a login
   stops working, log in again in the canonical checkout; do not restore an
   older copy.
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
   shows that, the premise is wrong for that CLI and this step needs revising.
4. Start sandboxes and subprocesses with the selected variables only, passed by
   name or through the tool's own channel; check that no credential value
   appears in a command line, a script's argument list or a logged command.
5. Before writing a tracked file, commit, Issue, PR or log, check that it holds
   no credential value and no path outside the project.
6. After a probe settles a fact about a credential, record it in the device's
   inventory row (`verified`, `scope`, `notes`).

## In each worktree

The same `CREDENTIAL_DIR` is a link to the canonical checkout's directory.
`setup-worktree.sh` creates that link when the canonical checkout has the
directory. A worktree never holds a login of its own, never logs in, and never
restores a login from a snapshot. `migrate-assets.sh` (used by worktree
teardown) drops the link and never copies a login; a real copy of a login
inside a worktree blocks the migration until someone checks it by hand. A
project whose setup hook links further login directories into `.project/` (the
home of another agent CLI, a proxy's tokens) gives each one a `login` rule in
`.agents/scripts/migrate-project.rules`, so teardown treats it the same way.
