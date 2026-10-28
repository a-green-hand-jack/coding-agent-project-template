# Four writing cases

These are invented, project-neutral examples, not execution evidence. Apply
the [common principles](../SKILL.md#common-principles) in the project's language.

## Issue: make acceptance executable

**Weaker:** “Improve export reliability. Tests and applicable live runs pass.”

**Rewrite:** “An interrupted export currently replaces the last usable file
with a partial one. Publish the replacement only after export completes;
preserve the last usable file on interruption. Acceptance includes an
interruption fixture that verifies the old bytes remain, and a successful
export through the public command that verifies the replacement can be read.
The requested live-run condition is still unresolved: before dispatch, the
scope owner must specify its entrypoint, conditions and terminal evidence, or
approve a scope change with a reason. The fixture alone cannot settle it.”

**Why:** The problem, intended behavior and known checks are concrete. The
rewrite exposes the missing decision without deleting a real-run requirement
or claiming that a fixture proves live behavior. When acceptance is already
clear, proceed without adding another confirmation step.

## PR: explain behavior and preserve conflicting evidence

**Weaker:** “Use rename in the exporter. All checks pass. Worker A implemented
this with no re-dispatch.” The Issue records a re-dispatch to worker B.

**Rewrite:** “Interrupted exports now leave the previous file readable. The
exporter writes a sibling file and renames it only on success, keeping the
replacement on the same filesystem. The interruption fixture passed at head
`<head-A>` using `<command>` under `<conditions>`; after the final edit, head
`<head-B>` still needs that check. Execution provenance is unresolved: this
PR names worker A with no re-dispatch, while the Issue records worker B.
The coordinator will reconcile the original session/run receipts before
claiming the final worker or live-run result.”

**Why:** Lead with reader-visible behavior, retain the implementation reason
and attach results to the head they actually tested. Contradictory Dispatch
records cannot establish which worker did the work. Replace the placeholders
with inspected facts in a real PR; a prose rewrite is not a passing check.

## Comment: anchor a new result and next action

**Weaker:** “Still testing. The current release works after I fixed my assertion.”

**Rewrite:** “The successful-export check passes for candidate `<head>` on
`<platform>`, compared with release `<version>`: `<command>` exits 0 and the
output reopens with the expected records. This establishes successful export,
not interruption recovery. The reviewer next checks the interruption receipt
for this same head before deciding merge readiness. The local assertion was
corrected without changing candidate source; diagnostic details are linked.”

**Why:** The result changes a specific judgment, keeps the baseline fixed and
names the next action. It does not carry a historical pass forward to a newer
head or hide a remaining failure behind a check-script correction.

## Commit: identify the actual change

**Weaker:** `Update export code`

**Rewrite:**

```text
Preserve the previous export when a replacement is interrupted

Write a sibling file and rename it only after completion so consumers
can keep reading the last successful export. Keep both on the same
filesystem for the replacement operation.

Refs: <issue>
```

**Why:** The title identifies a change from the history list; the optional
body preserves the reason and constraint. The prefix and language follow the
project. A small wording fix can simply say `Correct the export option name
in help`; it needs no long report, visual or forced prefix.
