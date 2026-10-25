---
name: template-work-runs-on-pi-deepseek
date: 2026-10-23
source: maintainer decision in the coordinating session, 2026-10-23; Issue #101 (series resolution instead of a fixed model string)
scope: project
applies_to: this template repository's Issue dispatch
status: active
supersedes: null
superseded_by: null
---

# Template work runs on Pi with DeepSeek

## Decision

Template maintenance is dispatched as a Pi agent on the provider configured for
Pi on this machine, with the newest available model in the `deepseek-v4.1-flash`
series. Template changes are usually small, so the cheaper agent is enough and
Claude Code is not the default here. The tier's model is resolved at dispatch
time rather than copied from an earlier Issue: list the models Pi and the
account currently offer, discard what is unusable (retired, out of quota, not
capable of the tier's work), take the newest `deepseek-v4.1-flash` member, and
record the resolved string. The Issue's Dispatch section names the agent,
provider, model and effort actually used, and the `issue-workflow` fallback and
re-dispatch rules still apply when an Issue turns out harder than it looked.

## Why

The template's Issues are mostly one or two files of skill, memory, registry or
script text with the change already spelled out, so paying the expensive tier
bought little. Keeping the choice in the Issue record keeps it reviewable, and
keeping the existing re-dispatch rule means a hard Issue is never blocked by the
default. A fixed model string ages: the series moves on, an account's quota
changes, and a dispatch that copied yesterday's string either fails or runs a
model the account can no longer use. Resolving the series at dispatch time keeps
the choice current without editing this record for every release.

## Apply

Start the Issue session with `--kind pi` and Pi's own model arguments. The
provider is the one Pi is configured with on the maintainer's machine; its name
is recorded in the Issue's Dispatch section and stays out of this tracked record.

```bash
herdr agent start tpl-issue-<N> --kind pi --pane <pane> -- \
  --provider <the provider configured for Pi on this machine> \
  --model <newest usable deepseek-v4.1-flash model> --thinking <effort>
```

Before starting, resolve `<newest usable deepseek-v4.1-flash model>`: ask Pi for
the models it can currently use, discard what the account cannot use or what is
excluded, take the newest member of the series, and write the resolved string
into the Dispatch section. Map the tier effort onto Pi's thinking levels (`low`,
`medium`, `high`, `xhigh`, `max`). If an Issue needs design or touches
credentials, isolation or concurrency, re-dispatch with a stronger agent and
record the reason, as `issue-dispatch-by-difficulty` requires.
