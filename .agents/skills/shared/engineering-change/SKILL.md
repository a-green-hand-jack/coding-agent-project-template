---
name: engineering-change
description: Design, implement, debug and refactor code with evidence proportional to the change.
---

# Engineering change

Use this skill when implementing a code change, investigating a defect or
refactoring behavior. Adapt the checks to the affected behavior and risk; finish
the full authorized outcome rather than treating a smaller edit as the goal.

1. Identify the observable outcome, affected interfaces, data and state owners.
   Understand the existing design before choosing a change. Remove unnecessary
   complexity where doing so helps the requested outcome; do not redesign unrelated
   code or add tooling solely because a task is difficult.
2. For a defect, reproduce the failure when feasible and establish why it occurs.
   Preserve useful failure evidence, fix the cause and verify the original
   scenario. If reproduction is impractical, state the evidence and limitation.
3. Model important state and validate external inputs at their boundaries. Where
   retries or interruption are possible, consider idempotence and recovery; where
   concurrent writers matter, isolate state or enforce ownership. Apply these
   choices to the actual operation, not as universal architecture mandates.
4. Check meaningful behavior through the interface relevant to its users. Prefer
   tests that fail for the defect or behavioral regression they are meant to
   detect; when practical, observe the expected failure before the fix. Avoid
   tests that merely mirror implementation. Use other evidence when a useful test
   is not practical, and report its limits.
5. For refactoring, establish the behavior that must remain, change the structure,
   and verify that behavior still holds. Work in verifiable units while retaining
   responsibility for the complete requested scope.
6. Select existing complexity, duplication or mutation tools when they answer a
   concrete question and are available; do not impose fixed scores, introduce new
   dependencies or require exhaustive mutation testing by default. Report what
   was actually checked and leave unrelated findings outside the claimed result.

Inspired by [ub-mode](https://github.com/unclebob/ub-mode); this procedure is
independently written and selectively adapted to the template's workflow.
