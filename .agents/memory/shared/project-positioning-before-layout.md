---
name: project-positioning-before-layout
date: 2026-10-28
source: Issue #113
scope: shared
applies_to: template adoption and Issues that change project structure
status: active
supersedes: null
superseded_by: null
---

# Understand the product before choosing its layout

## Decision

State who the project serves, what it delivers, its core concepts and non-goals
before designing paths or dispatching structural work. Product concepts govern
the layout; adopting three planes alone does not establish the right product.
Map existing paths to their destinations across product, development, human
documentation, runtime state and assets, reading affected directory contracts.
No domain taxonomy or wholesale test relocation follows from this template.

README owns positioning and navigation, USER owns usage, DEV owns extension and
maintenance. Memory keeps decisions and reasons and links to those authorities.
The product remains independent of the development plane. An adaptation records
an authorized resolution; it cannot authorize a contract conflict itself.

## Why

A tidy directory tree can still deliver the wrong thing. Root-only reading misses
local constraints, while experiment batches and copied development notes obscure
stable product concepts. Explicit positioning and path ownership expose those
errors before migration or parallel implementation makes them expensive.

## Apply

Use `template-adoption` steps 2–4 and `issue-workflow`'s structural Issue scope
check. Keep the project's actual positioning in its README, not in this record.
