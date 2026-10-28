---
name: development-writing
description: Write or revise Issues, PRs, comments and commit messages around reader decisions, current facts and traceable evidence.
---

# Development writing

Use this skill for development records. Read the relevant example in
[four writing cases](references/four-cases.md) when drafting or reviewing that
kind of text. Release preparation and its rendered-page/version checks remain
in [release-doc-audit](../release-doc-audit/SKILL.md), which uses the common
principles below. Writing or reviewing never authorizes a commit, send, push,
PR, merge or publication.

## Common principles

- Organize around the judgment the reader must make: lead with the problem,
  changed behavior or new conclusion, then explain cause, consequence and
  evidence. Keep useful technical detail where it supports that judgment.
- Make the body understandable without opening its links. Keep applicable
  Issue, PR, fixed code/version, result and comparison references for tracing
  claims; temporarily hide links to review comprehension, then restore them.
- Match each claim to evidence actually inspected. Give the relevant head or
  version, command/method, conditions, result and limits. Historical tests stay
  historical; fixture, live run, build and publication establish different
  things. A previous head's pass does not validate a new head. A historical
  client observation is not a rule for every version.
- Preserve unresolved facts and acceptance requirements. Identify conflicting
  records and what evidence/owner can resolve them; do not guess execution
  provenance or turn an ambiguous real-run requirement into an exemption.
  Resolve a genuine scope decision with its owner; already clear scope needs
  no additional approval. Never polish a pending decision into a completed one.
- Scale to the task: a small change may need only a sentence and a check.
  Use a table, diagram or image when it explains a comparison, relationship or
  result; no visual, fixed length or large form is required for every record.
  Label schematics and historical excerpts; retain the strengths of a source
  rather than judging a whole record by a weak excerpt.
- Keep secrets, private data, machine paths and raw private logs out of public
  prose and artifacts. Preserve existing authorization, redaction and
  acceptance rules; writing quality cannot replace them.

## What each record must do

Include the information needed for this task, without manufacturing empty
sections. Keep project templates and required machine-readable markers intact.

| Record / reader's question | Information to supply | Maintenance and common pitfall |
| --- | --- | --- |
| Issue: What problem, scope and completion are we agreeing to? | Concrete trigger and consequence, goal, constraints/tradeoffs, in/out scope, executable acceptance with entrypoint, conditions and expected evidence. Separate implementation and acceptance dependencies where relevant. | Update the body when scope/acceptance changes and retain important decisions in comments. “Applicable real run” without an applicability rule leaves a decision unresolved. |
| PR: What will this final change do, and can I merge it? | Before/after behavior, reason for the implementation, final scope, applicable Issue/fixed code/results, checks and evidence boundaries, related defects fixed. | Rewrite title and body around the final implementation when it changes. Preserve important decisions in comments; do not leave an abandoned plan or conflicting Dispatch as current fact. |
| Comment: What new fact changes my judgment or next action? | New result or decision first, impact, exact baseline/head/run and conditions when relevant, evidence and next action with an owner when responsibility is unclear. | Add material changes rather than repeat unchanged status. Correct a mistaken earlier claim explicitly; keep its history. “Current release” and debugging chronology obscure a durable conclusion. |
| Commit: What coherent change does this history entry identify? | Title states the actual behavior/rule change; body explains motivation, constraints and applicable references when the title/diff alone would not. | Match the message to the final diff before committing. Do not rewrite existing history merely to improve prose. “Update docs” identifies a topic, not the change; a full PR acceptance report is usually unnecessary. |

Current bodies and chronological comments serve different purposes: update an
Issue's agreed scope and a PR's final behavior, while recording significant
changes and reasons in comments. Do not silently erase a disputed claim or
retrospectively assign a later outcome to an earlier check. If evidence is
unavailable, state the conflict and concrete next action instead of claiming
resolution. A comment that only repeats status is useful only when an explicit
reporting obligation calls for it.

## Language and adaptation

Use the project's `writing.language` and `writing.issue_sections` through
[issue-workflow](../issue-workflow/SKILL.md#writing-conventions). Commit messages
also use that working language by default. A project that needs a different
commit language or title convention declares it in this skill's trailing
adaptation section; without a language declaration keep the existing language.
Do not impose Conventional Commits unless the project chooses it. Shared skill
text and its illustrative examples stay in the template's language; they do
not determine the language of records written using them.

Projects put slot values or step additions only in a trailing adaptation
section as described by [template-adoption](../template-adoption/SKILL.md).
Keep concrete historical examples outside this shared package and classify
them separately in the registry; they are not downstream rules.
