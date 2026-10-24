---
name: credential-inventory
date: 2026-10-24
source: .agents/scripts/probe-credentials.sh, setup-worktree.sh and diagnose-environment.sh as released in v0.1.16 (Issue #70), and their tests in the template's .agents/tests/test_template_credentials.py; moved here from llm-credentials in Issue #87
scope: shared
applies_to: repositories that adopt llm-credentials and name their credentials in a device inventory.yaml and a project credentials.yaml
status: active
refresh_after: when probe-credentials.sh, setup-worktree.sh or diagnose-environment.sh change what they read, check or print, or when the inventory or credentials.yaml fields change
supersedes: null
superseded_by: null
---

# Credential inventory, credentials.yaml and probes

The decisions behind these files are in
[`llm-credentials`](../../memory/shared/llm-credentials.md); the steps that use
them are in
[`credential-setup`](../../skills/shared/credential-setup/SKILL.md).

## Fact

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
status and the provider's error code. A row without one is not probed.

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

## Evidence

The usage comment at the top of `.agents/scripts/probe-credentials.sh` and its
`--check` and probe code paths; the calls to it in `setup-worktree.sh` and
`diagnose-environment.sh`. In the template repository,
`python3 -m unittest discover -s .agents/tests -p 'test_template_credentials.py'`
exercises both modes against fake inventories and a local HTTP endpoint.

## Refresh

Re-read the script's usage comment and the two callers whenever one of them
changes, and update this record in the same change.
