---
name: harvest-decisions
date: 2026-10-24
source: the ten per-run harvest records from 2026-10-13 to 2026-10-23, merged in Issue #87 (their text is in Git history); the run reports in the ignored .project/runs/harvest-<date>/
applies_to: this template repository's maintenance of its downstream adopters
---

# Lasting decisions from downstream harvests

## Decision

`template-harvest` runs before every release. What one run found, counted and
landed lives in its report, the release notes and `adopters.yaml`; this record
keeps only the decisions a later run must not take again. Candidates that were
looked at and not taken up, with the class they received:

- **"Plan the whole Issue, then implement it in steps."** Already upstream: it
  duplicates the existing rule to settle scope in the Issue before implementing,
  and phases are sub-Issues of one plan (`issue-workflow`, Phased work).
- **A record of a team mirror remote.** Project-local, even when two adopters
  wrote one: the mirror is the adopter's own infrastructure.
- **An adopter's task-routing rules for its own roles.** Project-local: they
  route that project's roles, and the template writes no rule for a particular
  role or task.
- **A settled adopter's own layout of template content** (memory records in one
  flat file, registry entries collapsed together, a credential directory at the
  repository root). Drift for that adopter's next `template-upgrade`, not a
  registry model change to bring upstream.

## Why

Until Issue #87 every run wrote its own memory record. The ten records repeated
the release notes, `adopters.yaml` and the run reports, and their reasons
mostly said only that the release checklist requires a harvest. The rules they
settled about the harvest itself are in `template-harvest`. What was left is
which candidates were declined and why; without a record, a later run proposes
them again from the next adopter that carries them.

## Apply

In step 3 of `template-harvest`, check a candidate against this list and give a
match the same class, citing this record. Step 4 says when to add an entry:
only for a lasting decision, written with counts and generic wording, never
with an adopter's name. A candidate that only one adopter has and that is still
being watched stays in `adopters.yaml` and the run report, not here.
