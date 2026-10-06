# Development resources

`.agents/` is the coding agent development plane. It is not product payload and
must not be copied into a product image or release artifact.

- `memory/`: durable project decisions, corrections and lessons;
- `knowledge/`: dated facts that can change, with source;
- `skills/`: repeatable procedures;
- `scripts/`: worktree setup, diagnostics, asset migration and teardown;
- `tests/`: small regression and seam checks for development.

Read the root `AGENTS.md` before acting. Read only the memory, knowledge and skill
files relevant to the current task. Keep the human conversation small by putting
durable context in the repository, not in an agent's private memory.
