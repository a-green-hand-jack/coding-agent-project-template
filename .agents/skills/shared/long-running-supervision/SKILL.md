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
7. Do not change code under a live run. A run that loads code from its checkout
   whenever it (re)starts a step fails on a half-merged or half-edited file, and
   bash reads a running script by byte offset, so editing that script in place
   corrupts the run. Make code changes and merges for a live run in another
   worktree. When a script in the running checkout must change, write the new
   version to a new file in the same directory and rename it over the old one
   (`mv new old`); never edit it in place. Before pulling or merging into a
   checkout, check it with the monitor entrypoint, and wait while a run is live.

Adapt the command names and receipt schema to the concrete product, but preserve
the read-only observation and recoverability boundaries.
