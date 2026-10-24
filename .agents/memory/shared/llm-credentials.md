---
name: llm-credentials
date: 2026-10-15
source: Issue #23 (policy); Issue #27 (per-canonical-checkout decision by the template maintainer); Issue #31 (safe re-login); Issue #59 (no credentials in command-line arguments); Issue #70 (inventory, probes and credentials.yaml); Issue #87 (steps moved to credential-setup, formats to credential-inventory)
scope: shared
applies_to: repositories whose code, tools or agents call LLM providers with API keys, tokens or OAuth logins
status: active
supersedes: null
superseded_by: null
---

# Manage LLM credentials across projects

The steps that apply these decisions are in
[`../../skills/shared/credential-setup/SKILL.md`](../../skills/shared/credential-setup/SKILL.md);
the formats of `inventory.yaml` and `credentials.yaml` and what
`probe-credentials.sh` checks are in
[`../../knowledge/shared/credential-inventory.md`](../../knowledge/shared/credential-inventory.md).

Related: [`third-party-llm-compat-patches.md`](third-party-llm-compat-patches.md)
(compatibility changes to third-party LLM tools) and
[`../../knowledge/shared/gpt5-strict-backend-requests.md`](../../knowledge/shared/gpt5-strict-backend-requests.md)
(request shapes strict backends reject). Read them together when a project
calls an LLM provider or relay.

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
   agent CLIs. Each project logs in itself, into a Git-ignored directory
   `CREDENTIAL_DIR` under the canonical checkout's `.project/`. The
   project's worktrees link to that directory and never log in again. Never
   link, copy, snapshot-restore or lend a login to another project.
3. **The project stays self-contained.** Code, configuration and documentation
   reference only paths inside the project. The shared file is reached through a
   symlink in a Git-ignored project directory. Credential values never enter Git,
   logs, Issues or PRs.
4. **Hand over only what is needed, never on the command line.** When passing
   credentials to a sandbox or subprocess, the project selects the variables
   that process needs and never passes the whole shared file. A credential never
   travels as a command-line argument: every local user can read a process's
   arguments through `ps`. Pass it as an environment variable selected by name
   (`docker run --env KEY`, with no value, copies `KEY` from the caller's
   environment) or through the tool's own environment or configuration channel
   (for git headers, `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>` and
   `GIT_CONFIG_VALUE_<n>` instead of `git -c http.extraHeader=...`).
5. **Every credential is known by name, never by value.** Each device keeps an
   `inventory.yaml` beside the shared file, mode 0600, with one row per variable
   of the shared file and its empty placeholders marked. A project keeps a
   tracked `credentials.yaml` that names the rows it needs. A read-only probe
   reads a value in its own process and prints only a status line.
6. **Account-bound settings that are not secret belong to the inventory row.**
   Its `endpoint` and `scope` are authoritative. A project overrides them on one
   machine only in the ignored `CREDENTIAL_DIR/overrides.env` and names the
   override in `credentials.yaml`. A knowledge record about a provider cites the
   inventory row by variable name and does not repeat its endpoint or scope.

## Why

Projects that each invented their own handling kept logins outside the
repository, copied API keys into per-project `.env` files or linked one
project's login from another. Two failures followed. Two consumers sharing one
refreshing login invalidate each other once both refresh, because a refresh
token such as Codex's is single-use. Restoring an older snapshot of a refreshing
login over a newer one silently overwrites the refreshed token. Stable keys do
not have this problem, so one guarded copy per device is enough for them.

Adopters that passed keys as `docker run -e KEY=<value>` or a header through
`git -c` exposed them to every local user for the life of the process, because
arguments are world-readable in `ps` while a process's environment is readable
only by its owner and root.

A shared file of bare `KEY=value` lines left agents unable to say what a
device holds without reading it. Two empty placeholders were taken for usable
keys; one key worked only on its account's own endpoint, one could generate but
not list models, and a used-up monthly budget answered `401 api_key_expired`,
indistinguishable from a broken key. Those facts, and which tool reads a key
under which name, ended up in Issue comments. Facts about a credential belong to
the credential, once per device, so that every project reads the same ones.

The worktrees of one project are one consumer. Each reads the same login through
its link, so a refresh made in one session is seen by all of them. A login per
worktree would need a new login for every worktree and would be lost with it.

## Apply

Each project fills two parameters, and writes its own additions to a step of
`credential-setup`, in the `## In this repository` section at the end of this
record (see `template-adoption` step 5):

- `SHARED_CREDENTIAL_FILE`: the device's shared file, taken from user-level
  configuration. If the device has none, the project runs without it.
- `CREDENTIAL_DIR`: the name of the Git-ignored directory under the canonical
  checkout's `.project/` that holds the symlink to the shared file and the
  project's own logins. This project uses `credentials`.

Then follow `credential-setup` in the canonical checkout and in each worktree.
