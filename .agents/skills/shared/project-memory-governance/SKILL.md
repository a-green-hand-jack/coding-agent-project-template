---
name: project-memory-governance
description: Classify, register, update and clean shared project development knowledge.
---

# Project memory governance

Use this skill after a user decision, a correction, a repeatable procedure or a
fact that future sessions would otherwise need to rediscover.

1. Search the project's memory, knowledge and skills indexes for an existing entry.
2. Classify the information:
   - **memory**: a durable decision, principle or lesson and its reason;
   - **knowledge**: a dated fact that may change and its source;
   - **skill**: a repeatable procedure with commands, evidence and failure limits.
3. Check the content registry. Mark the entry `shared` only if it does not depend
   on a product name, repository path, machine, provider, benchmark or private
   decision. Otherwise keep it project-specific.
4. Create one focused dated entry, record who decided it, why it matters and how
   future work should apply it. Update the matching README index in the same change.
5. When cleaning up, find inbound links and competing rules first. Supersede an
   old entry with a pointer to the replacement or remove it only when its history
   is already preserved by Git and no current link depends on it.
6. Review the resulting diff for secrets, private paths and duplicated rules.

Private agent memory can hold session progress, but it never counts as project
memory until the repository entry exists.
