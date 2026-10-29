---
name: project-memory-governance
description: Classify, register, update and clean shared project development knowledge.
---

# Project memory governance

Use this skill after a user decision, a correction, a repeatable procedure or a
fact that future sessions would otherwise need to rediscover.

1. Read `.agents/AGENTS.md`, the registry and relevant inbound links before
   choosing a destination. Its six-category contract covers execution, tests,
   memory, knowledge, skills and scripts, each with shared/project governance
   and relative CLAUDE links. Keep product/human/state/asset boundaries intact.
2. Give each piece one authority: memory for decisions/reasons/history, knowledge
   for current sourced facts, skills for procedures, AGENTS for routing/boundaries.
   Retain unique evidence; filename similarity is never a deletion criterion.
3. Choose physical shared/project separately from reuse scope. Template-only
   maintenance remains `scope: template` even inside project/. Empty shared
   groups are valid. Use the contract's kebab-case/Python snake_case/test_ naming;
   date only evidence and preserve month-only dates. Register required standard,
   lockfile or vendor names with reasons rather than silently exempting them.
4. Register each independent document or package once, with a stable ID, path,
   kind, scope, owner, summary, status, source and updated date (or explicit
   unknown). Keep lifecycle/ownership/replacement IDs in registry; body
   frontmatter owns content-specific sources/dates/applicability. Knowledge adds
   refresh_after; adapted content adds adaptation guidance and keeps its trailing
   local section. Never infer historical metadata without evidence.
5. Before moving, merging, extracting or retiring content, freeze from/to arrays
   of IDs/paths with action, rationale, source commit and verification in the
   existing registry's migrations. Cover all prior entries and tracked paths,
   including keep/empty/history dispositions. Preserve retired records, optional
   rejection and adaptation decisions. Stable IDs survive rename; many-to-many
   content reconciliation is reviewed explicitly. No competing ledger.
6. Update callers/imports/CI/discovery and adoption/upgrade together. Generate
   group indexes with `bash .agents/scripts/shared/check-development.sh
   --write-indexes`; do not hand-maintain duplicate summaries. Check normalized
   test discovery and all nested Shell scripts when paths change.
7. Run the official check without write flags. It must reject unregistered or
   ambiguously owned content, dangling entries, bad CLAUDE links/Git modes,
   unjustified names, stale indexes and dangling/cyclic replacement chains.
   Validate actual old-release migration and repeat-upgrade behavior for schema
   changes. Keep original historical sources and report exact command exits.

## Migrating legacy single-file records

For a downstream repository whose `memory/AGENTS.md` or `knowledge/AGENTS.md`
contains dated records, preserve the original text in Git history, split each
topic into a file under `shared/` or `project/`, add the required front matter,
and replace the old body with rules plus a short index. Classify each record
independently; do not infer `shared` merely because the old file was copied
from this template.

Private agent memory can hold session progress, but it never counts as project
memory until the repository entry exists.
