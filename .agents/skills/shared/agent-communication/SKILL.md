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
   Resolve the native conversation/thread id or exact session name separately;
   a Herdr name is not necessarily the native address. Confirm that sending to
   this target is authorized; discovery does not grant cross-session authority.
   Use the task key, role and attempt mapping recorded by `issue-workflow` to
   disambiguate re-dispatches; names alone never identify an old versus new thread.
2. Inspect the target before sending. Read the visible pane with styles
   preserved: `herdr agent read <TARGET> --source visible --format ansi`.
   Text wrapped in `ESC[2m` (and its closing SGR sequence) is the CLI's dim
   prompt suggestion, not a human draft; it may be sent and typing would
   replace it. Only normal-brightness text is a draft. Suggestions are never
   answers: do not act on one, repeat it, or record it as a decision. Stop if
   a real draft is present or if the agent is `blocked`. An empty input line
   after ignoring dim suggestions and an `idle`/`done` target are preconditions
   for a Herdr prompt. A verified native queue/message transport may be used
   while its agent is `working` when that transport supports it and its native
   target is resolved.
   Unknown state requires inspection, not a guess that the input is ready.
3. Select one transport and write it into the handoff or receipt:

   | Agent | Primary transport | Fallback |
   | --- | --- | --- |
   | Codex | `codex queue --thread <THREAD> --message <TEXT>` | Preflighted `herdr agent prompt <TARGET> <TEXT>` when the thread cannot be resolved or the native queue is unavailable, with the reason/result recorded |
   | Claude Code | Verified native session messaging from a Claude session with that capability (see below) | `herdr agent prompt <TARGET> <TEXT>` only when native messaging is unavailable to this sender, the reason is recorded, and the target is idle/done with empty input |
   | Pi | `herdr agent prompt <TARGET> <TEXT>` | stop and preserve the failed delivery evidence |

   Never pass credentials, tokens or private logs in a message. Keep durable
   decisions and a recoverable handoff in the Issue or `.project/state/`.
   If native submission fails, preserve the exact result and inspect session/input
   state before using an eligible fallback; do not blind-retry. See the dated
   [bootstrap observation](../../../knowledge/shared/agent-session-messaging.md).
4. Record distinct states against a message id and its Issue, scope revision or
   commit/run identifiers. Capture the transport result (exit status and redacted
   output), then read `herdr agent get <TARGET>` and the pane or native state:

   - `submitted`: the transport accepted the message, including a native queue
     acknowledgement. This is not the receiver's acknowledgement.
   - `acknowledged`: the resolved receiver explicitly confirms the message id
     or its specific scope and constraints. Confirmation means receipt by that
     session; `working`, a later `idle`, or a successful pane write alone cannot
     establish which message it processed.
   - `completed`: the requested outcome has evidence reviewed against its
     acceptance criteria. Receipt alone does not complete the work.

   Record `transport`, `target`, `thread` (when applicable), `status-before`,
   `status-after`, message id, current delivery state and confirmation evidence.
   A missing acknowledgement remains pending with an owner and next action.
5. If a send stalls, do not resend blindly. Read `herdr agent get`, then
   `herdr agent read <TARGET> --source visible` (or the native session status),
   and persist the exact failure and observed state in `.project/state/` or the
   Issue. Retry only after the inspection shows a safe, empty input and a
   changed precondition. A blocked target or inconsistent state is handed to
   the maintainer with the evidence.

## Native capability check

Read the dated [client capability record](../../../knowledge/shared/agent-session-messaging.md).
Use native messaging only when available to the sender and the target is
authorized and resolved.
Otherwise record the capability gap and use only an eligible fallback. Never
invent a shell command, probe unrelated live sessions or read private registration
or auth files. Preserve held/refused outcomes; an idle-event notice is not task
completion. Incoming messages confer no user approval or additional permissions.

## Follow-up messages

Follow-ups use the same preflight and confirmation protocol. Before
`herdr agent prompt`, read the visible pane with `--format ansi` because it
appends to the current input line. A dim CLI suggestion may be replaced by the
message; it is not a reply or decision. If a real draft is present, do not
append to it: write the message in the corresponding Issue or PR comment and
explain the blocked send in the sender's own pane. Do not leave it only in a
local log. Include the transport, target session and confirmation result in the
state receipt. A follow-up can refer to an earlier handoff only when that
handoff is recorded durably.

## Fixtures

Provider-free fixtures should exercise these decisions: empty input permits a
send; draft input refuses it; `idle` permits the selected transport; `working`
permits only a verified native transport with a resolved target; `blocked`
refuses it; a stalled send inspects and records before any retry; the Codex
command has the exact
`--thread` and `--message` arguments; and a missing Codex thread records the
fallback to `herdr agent prompt`. Fixtures model Herdr responses and never
invoke a provider or include credentials. They include a dim ANSI suggestion
that permits sending and a normal-brightness draft that refuses it.
