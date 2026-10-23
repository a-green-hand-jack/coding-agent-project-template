---
name: look-at-the-artifact-before-concluding
date: 2026-10-23
source: Issue #76, harvested from a downstream adopter of this template
scope: shared
applies_to: projects that produce generated artifacts (images, video, audio, text, data) and accept them with automatic metrics
status: active
supersedes: null
superseded_by: null
---

# Look at the artifact itself before reporting a result

## Decision

Before reporting the result of a generation or an evaluation, look at the
artifacts yourself: put sampled outputs next to their references, listen to
audio, read text. Only then read the scores. Automatic checks, including a
cross-check between models, are leads, not acceptance evidence. When the
artifacts and the scores disagree, suspect the measurement first. The report
states which artifacts were looked at.

## Why

Two cases from one downstream project. A generation pipeline produced output
unrelated to its reference while the automatic score was close to perfect; a
person looking at the output found it, and a whole stage that validates the
scorer was added afterwards. In another case, reference images and their
descriptions passed a perceptual-hash check and a cross-check by two models;
comparing them against the source frames showed the colors were wrong, and the
"correction" had introduced a new error. A metric measures what it was built to
measure, and a pipeline can satisfy it without producing what it was meant to.

## Apply

- Sample enough outputs to cover the variation the run produced, and view each
  next to its reference or input. A viewer you cannot use (audio, video) is a
  gap to name, not a pass.
- Treat a surprisingly good score as seriously as a bad one: look at the
  artifacts behind it before accepting it.
- When looking and the score disagree, check the metric, its inputs and its
  wiring before changing the pipeline.
- In the report, list the artifacts looked at and what was seen, separately
  from the scores.
