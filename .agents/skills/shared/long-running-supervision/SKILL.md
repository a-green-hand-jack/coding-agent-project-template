---
name: long-running-supervision
description: Observe and recover a product that runs longer than one interactive session.
---

# Long-running supervision

Use this skill when a product run can last minutes or hours, use background
workers, or create durable artifacts.

1. Start the run through the public CLI and record its worktree, state root,
   configuration, image or environment version, output directory and process
   identity in `.project/runs/`.
2. Run the long-lived command in a dedicated terminal, Herdr pane, tmux session or
   service. Do not block the human-facing coding session waiting for completion.
3. Provide one read-only status or monitor entrypoint. It should expose current
   state, progress, last activity, errors, artifacts and recovery hints without
   mutating the run or reading secrets.
4. Persist structured receipts and logs under the worktree state root. A terminal
   message or process exit code alone is not completion evidence.
5. Define checkpoint, stop, resume, retry and terminal-failure behavior. On
   restart, replay or reconcile durable results before starting duplicate work.
6. Report implementation, runtime acceptance and final artifact acceptance as
   separate verdicts.

Adapt the command names and receipt schema to the concrete product, but preserve
the read-only observation and recoverability boundaries.
