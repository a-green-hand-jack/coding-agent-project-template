---
name: screen-with-scriptable-fakes
date: 2026-10-23
source: Issue #80, from two downstream adopters that each built such a fake; placement decided by the template maintainer in that Issue
scope: shared
applies_to: repositories whose product calls a non-deterministic external boundary, such as a provider's HTTP upstream or an agent executor
status: active
supersedes: null
superseded_by: null
---

# Screen failure paths with a scriptable fake before the real run

## Decision

1. **Use one scriptable fake for the external boundary, not inline stand-ins in
   individual tests.** It is a single file, standard library first, that the
   product reaches through its normal configuration (a base URL or an executor
   setting).
2. **Write scenarios as data.** A scenario lists what the boundary does, in
   order: status codes with the upstream's exact wording, delays, a stream cut
   half-way, a dropped connection, no answer at all, redirects, `retry-after`
   headers and polling that completes after N calls.
3. **Record every request the fake receives, and mask credentials by key name.**
   Header and field names such as `authorization`, `api-key`, `token` and
   `secret` are replaced when the record is written, so the record never depends
   on knowing a credential's value.
4. **Cover both kinds of boundary.** A fake upstream covers provider HTTP calls;
   a fake agent executor, driven through the public CLI, covers interrupt →
   resume → terminal state, rerunning only failed steps, lock refusal, gap-free
   sequence numbers and signal handling.
5. **Write the scenario and a regression first when a boundary defect appears,
   then fix it.** The scenario stays so the failure replays.
6. **The fake is a sieve, not acceptance.** It stays out of the product tree and
   the image, does not replace a real container, protocol or OCI run, and never
   counts as completion evidence.

## Why

Boundary defects (an upstream rejection the client mishandled, a slow or cut
stream, a retry that ignored `retry-after`, a poll that never ended, a resume
that repeated finished work) used to surface only in real runs, which are
slow, costly and hard to repeat. Inline stand-ins in single tests could not be
reused across cases, and they did not show the request headers, which is where
several of these defects were. A scriptable fake makes the failure cheap to
reproduce and replay, and the request record shows what the product actually
sent. Because the fake is built by the project, it only reflects what the
project already believes about the boundary, so it cannot show that the real
boundary behaves that way.

## Apply

1. Decide whether the defect sits on the boundary (what the product sends, how it
   reacts to what comes back) or inside the product's own logic. Only the first
   needs the fake.
2. Write the scenario as data and a regression that fails before the fix. Keep
   the fake and its scenarios with the project's tests, not under the product
   tree or in the image.
3. Before a real run, run the scenarios once. A failure found there is cheaper
   than the same failure in the real run.
4. Take completion evidence from the real run's receipts and artifacts, as in
   [`long-running-supervision`](../../skills/shared/long-running-supervision/SKILL.md).
   A passing fake run is a reason to start the real run, not a result.
5. Before committing a scenario, request record or Issue text, check that it
   holds no credential value, account or machine-local path. See
   [`llm-credentials.md`](llm-credentials.md).
