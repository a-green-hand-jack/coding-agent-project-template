---
name: llm-credentials
date: 2026-10-15
source: Issue #23 (policy); Issue #27 (per-canonical-checkout decision by the template maintainer); Issue #31 (safe re-login); Issue #59 (no credentials in command-line arguments); Issue #70 (inventory, probes and credentials.yaml)
scope: shared
applies_to: repositories whose code, tools or agents call LLM providers with API keys, tokens or OAuth logins
status: active
supersedes: null
superseded_by: null
---

# Manage LLM credentials across projects

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
   agent CLIs. Each project logs in itself, for example
   `CODEX_HOME=<login dir> codex login --device-auth`, into a Git-ignored
   directory `CREDENTIAL_DIR` under the canonical checkout's `.project/`. The
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
4. Start sandboxes and subprocesses with the selected variables only, passed by
   name or through the tool's own channel; check that no credential value
   appears in a command line, a script's argument list or a logged command.
5. Before writing a tracked file, commit, Issue, PR or log, check that it holds
   no credential value and no path outside the project.

### Inventory, probes and credentials.yaml

The device's `inventory.yaml` sits in the directory of `SHARED_CREDENTIAL_FILE`,
mode 0600. Both files below use a small YAML subset: top-level `key: value`
lines and one `credentials:` list of flat mappings, one `key: value` per line.

```yaml
credentials:
  - variable: OPENAI_API_KEY            # the name in the shared file
    service: openai
    kind: api-key                       # api-key | oauth-token | subscription-key | repo-token
    purpose: daily account, evaluation judge
    endpoint: https://api.openai.com/v1 # provider default or the account's own base URL
    auth: bearer                        # bearer | header:<Name> | query:<name>
    scope: all models
    status: active                      # active | empty-placeholder | retired | rotate
    owner: <project that introduced it>
    verified: <date> GET /models
    notes: <quota, symptom when used up, region, data residency>
    probe: GET /models
```

Every variable of the shared file has a row, and an empty one is marked
`empty-placeholder`. `probe` is a read-only `GET <path or https URL>` against
`endpoint`, with the value applied as `auth` says and optional fixed headers as
`Name=value` tokens; it reports `ok` on a 2xx answer and otherwise the HTTP
status and the provider's error code. A row without one is not probed. After a
probe settles a fact, record it in the row (`verified`, `scope`, `notes`).

The project's tracked `credentials.yaml`, at the repository root, replaces the
free-form credential notes of `.env.example`, which keeps only the variable
names the code reads:

```yaml
shared_file: .project/credentials/<name>   # CREDENTIAL_DIR's link to SHARED_CREDENTIAL_FILE
credentials:
  - variable: GOOGLE_API_KEY               # an inventory row
    exposed_as: GEMINI_API_KEY             # the name the consumer reads, when it differs
    consumer: gemini CLI in the sandbox runner
    required: true                         # false: problems only warn
    overrides: GOOGLE_GEMINI_BASE_URL      # set in CREDENTIAL_DIR/overrides.env on this machine
```

- `bash .agents/scripts/probe-credentials.sh --check` reads no network. It
  reports a variable without a row, an empty variable not marked, and each
  project row that is missing, an empty placeholder, retired or unset.
  `setup-worktree.sh` runs it and fails on an error. With
  `--shared-file <path>` it checks a device's inventory without a project.
- `bash .agents/scripts/probe-credentials.sh` runs the probes and prints
  `credential <name>: ok | failed | not-probed (...)`;
  `diagnose-environment.sh` shows these lines and fails on a required
  credential that failed.
- A device without the shared file (a CI runner, another machine) only skips.
  A project that adopts this lists the variable names of its `.env.example` as
  the first draft of `credentials.yaml`.

In each worktree of the project, the same `CREDENTIAL_DIR` is a link to the
canonical checkout's directory. `setup-worktree.sh` creates that link when the
canonical checkout has the directory. A worktree never holds a login of its own,
never logs in, and never restores a login from a snapshot. `migrate-assets.sh`
(used by worktree teardown) drops the link and never copies a login; a real copy
of a login inside a worktree blocks the migration until someone checks it by hand.
A project whose setup hook links further login directories into `.project/` (the
home of another agent CLI, a proxy's tokens) gives each one a `login` rule in
`.agents/scripts/migrate-project.rules`, so teardown treats it the same way.
