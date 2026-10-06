# Development plane rules

This directory belongs to coding agent development. It never belongs in the
product runtime or release payload.

## Where information goes

- A durable decision, correction or project lesson goes in `memory/` and its
  index before it counts as recorded.
- A changing environment or external fact goes in `knowledge/`, with date and
  source.
- A repeatable operation goes in `skills/`.
- Product behavior belongs in the root product, user or developer documents,
  not here.
- Session progress may remain private; project knowledge may not.

Never store credentials, raw authentication files, private sessions or personal
data here.
