---
name: speed-and-parallelism-by-measurement
date: 2026-10-23
source: Issue #78, harvested from downstream adopters of this template
scope: shared
applies_to: repositories that dispatch Issues with the issue-workflow skill or run long product runs under the long-running-supervision skill
status: active
supersedes: null
superseded_by: null
---

# Default to the fastest safe way: parallel by independence, concurrency by measurement

## Decision

Speed is a first-class quality. A serial step that has no dependency, repeated
work and idle waiting are defects to remove, not caution. Independent units of
work run concurrently, and only a real dependency queues (a delivery that must
exist before it can be reviewed). The concurrency level is decided by measured
CPU, memory, disk and the provider's observed error rate, never inferred from a
container limit, a configured cap or the number of sessions. Efficiency means
removing repeated work, not skipping it. None of this relaxes verification,
correctness, credential or safety boundaries, or crosses an explicit spending
limit; a check is never skipped to look fast.

## Why

Downstream adopters each reached the same practice independently and kept it:

- Queueing independent units by arrival order left capacity idle while one unit
  waited for another it did not depend on.
- A concurrency level taken from a limit or a setting was wrong in both
  directions: too low where the host had room, too high where the provider
  started rejecting requests. A level chosen from measured resource use and the
  observed error rate was stable.
- Reinstalling the same toolchain for every run dominated the wall clock. Baking
  it into the base image and sharing the toolchain and caches per scope removed
  most of that time, and a snapshot reused a finished build instead of repeating
  it.

## Apply

- **Judge independence.** Two units are independent when neither needs the
  other's output, and they do not write the same state, file or external
  resource. Independent units start together, each in its own worktree and
  session or its own worker. A unit that needs another's delivery starts when
  that delivery lands, not before and not later. A fixed interface may release
  independent implementation while acceptance waits for merged behavior; those
  are separate scopes and dependencies, never permission to bypass a blocker.
  For Issues the dependency is
  recorded on GitHub as blocked-by, not in prose or in a coordinator's memory,
  so that every coordinator can read what is free to start
  (`issue-workflow`, Phased work).
- **Trigger downstream on delivery.** Start the dependent step (review, merge
  check, the next stage) from the upstream unit's receipt, not on a timer and not
  when the whole batch ends. Keep a rolling queue: when a slot frees, the next
  ready unit takes it.
- **Set concurrency by measurement.** Start low, raise the level while measured
  resources stay below saturation and the provider's error and rate-limit
  responses stay flat, and lower it when they rise. Record the measurements next
  to the chosen level. Never exceed a declared spending or quota limit to gain
  speed.
- **Report concurrency apart from time and cost.** A report gives the
  concurrency level, the wall-clock time and the cost as three separate numbers.
  Faster wall clock is not evidence of lower cost, and higher concurrency is not
  evidence of faster completion.
- **Remove repeated work first.** Before adding concurrency, preinstall what
  every run installs into the image, share toolchains and caches per scope, and
  reuse a snapshot of a finished build or step. Reconcile durable receipts
  before restarting work so completed units are not redone.
- **Keep the guards.** Concurrency never shares a credential that must not be
  shared, never writes into a live run's checkout, and never changes what a check
  verifies.

The skills `long-running-supervision` (scheduling and concurrency) and
`issue-workflow` (independent Issues in parallel) carry the procedure.
