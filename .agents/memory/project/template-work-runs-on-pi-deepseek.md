---
name: template-work-runs-on-pi-deepseek
date: 2026-10-23
source: maintainer decision in the coordinating session, 2026-10-23
scope: project
applies_to: this template repository's Issue dispatch
status: active
supersedes: null
superseded_by: null
---

# Template work runs on Pi with DeepSeek

## Decision

Template maintenance is dispatched as a Pi agent with the DeepSeek model.
Template changes are usually small, so the cheaper agent is enough and Claude
Code is not the default here. The Issue's Dispatch section still names the
agent, model and effort, and the `issue-workflow` re-dispatch rule still applies
when an Issue turns out harder than it looked.

## Why

The template's Issues are mostly one or two files of skill, memory, registry or
script text with the change already spelled out, so paying the expensive tier
bought little. Keeping the choice in the Issue record keeps it reviewable, and
keeping the existing re-dispatch rule means a hard Issue is never blocked by the
default.

## Apply

Start the Issue session with `--kind pi` and Pi's own model arguments:

```bash
herdr agent start tpl-issue-<N> --kind pi --pane <pane> -- \
  --provider <the provider configured for Pi on this machine> \
  --model deepseek-v4.1-flash-1017 --thinking <effort>
```

Map the tier effort onto Pi's thinking levels (`low`, `medium`, `high`, `xhigh`,
`max`). If an Issue needs design or touches credentials, isolation or
concurrency, re-dispatch with a stronger agent and record the reason, as
`issue-dispatch-by-difficulty` requires.
