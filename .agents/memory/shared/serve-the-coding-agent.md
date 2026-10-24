---
name: serve-the-coding-agent
date: 2026-10-24
source: Issue #85, from one downstream adopter of this template
scope: shared
applies_to: repositories that develop their own agent or workflow on top of an existing coding agent (Claude Code, Codex, Pi or similar)
status: active
supersedes: null
superseded_by: null
---

# Use the existing coding agent, and write what serves it

## Decision

Use the existing coding agent fully. What we develop is, in effect, service to
that agent: what it already does, we do not write again, and its judgment we do
not replace. Our five offerings to it:

- **Guidance**: it knows what counts as done, where the boundaries are and how
  a failure is recorded; the standard the instructions state is the one the
  checks and the review actually judge.
- **Tools**: mechanical work is handed to commands. A command's result is
  stable, composable and machine-readable, and when it fails it tells the agent
  what to do next.
- **Parallelism**: every run is isolated and shares no state that gets
  rewritten (for how to run in parallel, see
  [`speed-and-parallelism-by-measurement.md`](speed-and-parallelism-by-measurement.md)).
- **Trace**: every conclusion in a result traces back to a step, a command call
  and a file; a person can follow the whole process from one place.
- **Cost**: every run can say how much it spent and at which stage; a budget can
  be set, and a run that passes it stops.

The five are a lens for reviewing a change, not a feature list every project
must complete. Every change helps at least one of them. Code that helps none is
a candidate for deletion; anything that holds one of them up is not deleted to
make the code smaller.

## Why

The downstream adopter that brought this record to the template met these four
problems in real runs of its own:

- **A total token count does not show where the money went.** How many tokens a
  run spends depends mainly on how many turns went back and forth and how long
  the context carried in each of them was, not on how much material was read.
  The most expensive part, input that missed the cache and is billed at full
  price, sat in the final review stage, because review reads the record from the
  start again; in the total that stage looks small.
- **Parallel runs happened by luck, not by design.** The runs happened not to
  share files, so they could go at the same time; but building images, saving
  environment snapshots and reading and writing cold storage still crowded onto
  one machine and slowed each other.
- **Monitoring showed the steps, not the spending.** So no budget could be set,
  and nothing stopped a run that overspent.
- **Instructions, checks and review drifted apart.** Each was changed on its
  own: a requirement in the instructions was checked by no script, and a rule
  added to a script was not written in the instructions, so the agent was sent
  back repeatedly without knowing why.

What was missing, and what this record asks for: instructions and checks changed
together; accounting per run with a budget that can stop it; review reading a
prepared summary instead of the raw conversation record; and, before a shared
file, a global lock or a global cache is added, confirming that it does not turn
runs that could go in parallel into a queue.

## Apply

Each project fills five items in the `## In this repository` section at the end
of this record (see `template-adoption` step 5):

- `GUIDANCE`: where the instructions and the acceptance criteria live.
- `COMMANDS`: the commands the coding agent calls.
- `ISOLATION`: what keeps each run apart from the others.
- `TRACE`: where the run records are and where a person reads them.
- `ACCOUNTING`: where usage is recorded and where the budget stops a run.

Then:

1. When designing or reviewing a change, write down which of the five it helps.
2. When a check's rule changes, change the matching instruction in the same
   change; when an acceptance criterion changes, make sure a check or a review
   can judge it.
3. Account while the run is going, request by request (input that missed the
   cache, input that hit the cache, output); read the cost from the run record
   instead of assembling it later while writing a report.
4. Assemble the trace and the cost once: the raw conversation record is only
   the material, and review reads a fixed-format summary produced by a command.
5. Before adding a shared file, a global lock or a global cache, confirm that it
   does not turn runs that could run together into a queue.

A project not built on a coding agent needs nothing from this record.
