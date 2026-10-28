---
name: agent-session-messaging
date: 2026-10-28
source: >-
  https://code.claude.com/docs/en/cross-session-messaging;
  https://learn.chatgpt.com/docs/developer-commands?surface=cli;
  installed CLI help; coordinator-supplied Codex bootstrap observation for Issue 113
scope: shared
applies_to: naming and authorized handoffs between coding-agent sessions
status: active
refresh_after: when the client, naming or messaging capability, or delivery behavior changes; recheck before relying on a different installation
supersedes: null
superseded_by: null
---

# Native session messaging, naming and bootstrap limits

## Fact

Claude's native `ListAgents` and `SendMessage` tools discover and message other
sessions. Active recipients process messages between tool calls; an idle
recipient starts a turn. Inbound controls can deliver, hold or refuse a message.
`SendMessage`'s `notify_when_idle` input supports a notice when a local session
next becomes idle or exits. The notice reports a session event, not acceptance
of the task's outcome. These are session tools, not a general shell send command;
availability and receiver permissions must still be checked.

The official version minimum is v2.1.224 on macOS/Linux/WSL 2, v2.1.234 on native
Windows, and v2.1.236 in both sessions for idle notices. Provider/configuration
conditions also apply; version alone does not prove tool availability.

Naming evidence checked on the same date:

| Client | Supported surface and limit of the evidence |
| --- | --- |
| Claude Code | Installed v2.1.312 `claude --help` exposes `-n, --name <name>` for startup naming. |
| Codex | Installed `codex --help` exposes no `--name`; official OpenAI documentation specifies interactive `/rename <name>`. When that surface is unavailable, retain the thread ID mapping instead. |

In the coordinator's Codex observation, queueing before the first turn failed
with code `-32603` and the error fragment `no rollout found`. A preflighted Herdr
fallback successfully bootstrapped the first turn. A known thread ID therefore
did not alone prove the native queue was ready. This is one observed bootstrap
failure, not a universal restriction on Codex versions.

## Evidence

The [official Claude documentation](https://code.claude.com/docs/en/cross-session-messaging),
checked 2026-10-28: Message another session, Message delivery, Get a notice when
another session goes idle, and Availability. Naming sources are installed CLI
help and [official OpenAI developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli),
Rename the current chat with /rename, checked on the same date. The Codex
bootstrap evidence was supplied by the coordinator; it was not reproduced by
launching another session. No private transcript or session identity is included.

## Refresh

Recheck official documentation, installed CLI help and actual available tools
when `refresh_after` applies. Do not probe unrelated live sessions. Preserve an
authorized send's actual result before changing transport; never infer receipt
or completion from a successful submission or an idle notice. Apply the protocol
in [`agent-communication`](../../skills/shared/agent-communication/SKILL.md).
Naming procedure is in [`issue-workflow`](../../skills/shared/issue-workflow/SKILL.md).
