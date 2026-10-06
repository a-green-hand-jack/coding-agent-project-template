---
name: cli-first-operations
description: Make product operations discoverable and repeatable through one public CLI.
---

# CLI-first operations

Use this skill when adding or documenting setup, run, status, monitor, checkpoint,
resume, artifact or release operations.

1. Prefer the same public CLI that a user runs. Do not call private Python
   modules, provider SDKs or internal helpers as a second product path.
2. Give each operation one stable verb, explicit arguments and machine-readable
   output where automation needs it. Keep credentials out of arguments and logs.
3. Make errors actionable: preserve the exact failure, identify the boundary that
   rejected it and state the next safe inspection or recovery command.
4. If the public CLI lacks a capability, report the specific gap and agree on a
   formal CLI change. Do not build a temporary parallel launcher or monitor.
5. Verify the CLI from a fresh worktree environment, not only through an internal
   function call.

The CLI is the product's operational contract. Shell snippets are navigation and
diagnostics, not an alternate runtime.
