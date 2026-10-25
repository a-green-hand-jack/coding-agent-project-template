---
name: agent-communication
description: Route confirmed messages between Herdr panes and coding-agent sessions, using each agent's native transport and preserving recoverable handoffs.
---

# Agent communication

Use this skill when one coding-agent session needs to send a handoff or a
follow-up message to another session in a Herdr worktree. A pane is only a
terminal layout. An agent session is the process Herdr detects in that pane.
A conversation or thread is the agent's own message history. Resolve and
record all three separately; a successful write to a pane does not prove that
the agent received or started the message.

## Protocol

1. Resolve the target by its Herdr agent name or pane id. Read `herdr agent
   get <target>` and record the target name, pane, worktree and current state.
   For Codex also resolve the native conversation/thread id or exact session
   name before choosing `codex queue`.
2. Inspect the target before sending. Read the visible pane and stop if the
   input line contains a draft or if the agent is `blocked`. An empty input
   line is a precondition for a Herdr prompt. A Codex queue may be used while
   the agent is `working` only when its thread was resolved and the queue
   command itself succeeds.
3. Select one transport and write it into the handoff or receipt:

   | Agent | Primary transport | Fallback |
   | --- | --- | --- |
   | Codex | `codex queue --thread <THREAD> --message <TEXT>` | `herdr agent prompt <TARGET> <TEXT>` after recording that the native thread was unavailable |
   | Claude Code | `herdr agent prompt <TARGET> <TEXT>` | stop and preserve the failed delivery evidence |
   | Pi | `herdr agent prompt <TARGET> <TEXT>` | stop and preserve the failed delivery evidence |

   Never pass credentials, tokens or private logs in a message. Keep durable
   decisions and a recoverable handoff in the Issue or `.project/state/`.
4. Confirm delivery in two observations. First, capture the transport result
   (exit status and its redacted output). Then read `herdr agent get <TARGET>`
   and the pane or native session state. Confirmation means the target remains
   the resolved session and shows `working`, `idle` after processing, or a
   native queue acknowledgement. It does not mean that a command merely
   accepted bytes. Record `transport`, `target`, `thread` (when applicable),
   `status-before`, `status-after` and the confirmation evidence.
5. If a send stalls, do not resend blindly. Read `herdr agent get`, then
   `herdr agent read <TARGET> --source visible` (or the native session status),
   and persist the exact failure and observed state in `.project/state/` or the
   Issue. Retry only after the inspection shows a safe, empty input and a
   changed precondition. A blocked target or inconsistent state is handed to
   the maintainer with the evidence.

## Follow-up messages

Follow-ups use the same preflight and confirmation protocol. Before
`herdr agent prompt`, read the visible pane because it appends to the current
input line. If a draft is present, do not append to it; put the message in the
Issue or ask the maintainer to send it. Include the transport, target session
and confirmation result in the state receipt. A follow-up can refer to an
earlier handoff only when that handoff is recorded durably.

## Fixtures

Provider-free fixtures should exercise these decisions: empty input permits a
send; draft input refuses it; `idle` permits the selected transport; `working`
permits only a resolved Codex queue; `blocked` refuses it; a stalled send
inspects and records before any retry; the Codex command has the exact
`--thread` and `--message` arguments; and a missing Codex thread records the
fallback to `herdr agent prompt`. Fixtures model Herdr responses and never
invoke a provider or include credentials.
