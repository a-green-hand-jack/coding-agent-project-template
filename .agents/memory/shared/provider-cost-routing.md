---
name: provider-cost-routing
date: 2026-10-25
source: Issue #101 (maintainer decision on provider cost, agent dispatch and evidence)
scope: shared
applies_to: repositories whose tests, checks, coding agents or tools call LLM providers
status: active
supersedes: null
superseded_by: null
---

# Route provider and model cost first, and keep every cheap run real

## Decision

1. **Cost is a first-class routing constraint.** Ordinary tests, regression
   checks, documentation, mechanical edits and routine development use the
   cheapest token source and the cheapest model that can judge them.
2. **A cheap run is still a real provider-backed run.** The cheapest model may
   replace an expensive one to save money, never to substitute for the
   capability the acceptance must prove.
3. **The expensive provider or model is used only when the change concerns it:**
   its request format, authentication or permissions, model capability, quota
   and error behavior, or other real behavior only it exercises. The plan names
   that reason when a run upgrades.
4. **Agent, provider, model and effort are chosen in that order and passed
   explicitly.** The CLI's default is never relied on. The choice is recorded in
   the Issue's Dispatch section and, with what the run proves and why it must
   run, in the plan and the PR.
5. **Provider facts belong to the provider record, not to the plan.** Endpoint,
   scope, capability, quota and the date they were probed are kept in the device
   inventory or in a knowledge record and cited by name. Secret values never
   enter the repository, logs, Issues, PRs, command lines or plans.

## Why

A project that calls LLM providers pays for every check it runs. Two failures
follow when cost is not part of routing. Every ordinary test or mechanical edit
is sent to the most expensive provider and model, although a cheap one judges it
just as well. Or the opposite: a cheap model stands in for a capability check the
change actually needs, and the acceptance then records a pass that the expensive
provider's behavior was never exercised for. Issue #101 recorded this decision
after the dispatch records named a model and effort but not the provider, and
after the close-out steps did not say which run evidence had to exist before a
worktree was retired.

An implicit choice cannot be reproduced either: CLIs change their default model
and effort without notice, so a record that says only "the default" cannot be
judged later or repeated by another session.

## Apply

Follow Dispatch by difficulty and Start step 4 in
[`../../skills/shared/issue-workflow/SKILL.md`](../../skills/shared/issue-workflow/SKILL.md)
and the Issue session rules it prints: choose the agent first, then the provider
and model, then the effort, resolve a series to its newest usable member at
dispatch time, and record the result with its fallback or re-dispatch history.

The formats of the device inventory and the project's `credentials.yaml`, and
what a read-only probe checks, are in
[`../../knowledge/shared/credential-inventory.md`](../../knowledge/shared/credential-inventory.md);
the credential decisions that keep values out of tracked content are in
[`llm-credentials.md`](llm-credentials.md).
