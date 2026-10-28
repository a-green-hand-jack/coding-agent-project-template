---
name: agent-session-messaging
date: 2026-10-28
source: >-
  https://code.claude.com/docs/en/cross-session-messaging;
  https://learn.chatgpt.com/docs/developer-commands?surface=cli;
  installed CLI help; coordinator-supplied Codex bootstrap observation for Issue 113;
  Issue 127 scoped Linux caller-context and isolated-session observations
scope: shared
applies_to: naming, Codex caller-context isolation and authorized handoffs between coding-agent sessions
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

## Codex Herdr context observation (2026-10-28)

Issue 127 reports Linux, Codex CLI and inspected daemon both 0.165.0, Herdr
client 0.9.4/server 0.9.1. A tool environment carried obsolete pane/workspace
IDs while the visible current session occupied another verified pane. Read-only
inspection found the same stale identity in the daemon manager and app-server
child. The reported lookup errors were `agent_not_found`, `workspace_not_found`
and `pane_not_found`. This supports a retained-process-context diagnosis for
that observation; it is not proof that every version or shared daemon propagates
environment this way. Starting a daemon in pane A, retiring A and attaching from
B is a proposed causal reproduction, not an independently completed experiment.

The coordinator also observed all four `HERDR_*` identity variables missing.
Authorized read-only discovery recovered its ownership from current visible
messages/tool activity and Herdr-returned pane/worktree/repository identity.
This shows that missing variables do not prove a visible session is outside
Herdr. It does not establish the cause of missing context or count as a passing
isolated session. Do not generalize cwd or title matching into identity proof.

Installed `codex --help` exposes `--no-daemon` to avoid the shared background
server even when it is running; `codex queue --help` takes `--thread` and
`--message`. The [official command reference](https://learn.chatgpt.com/docs/developer-commands#global-flags)
also documents the isolation flag. These capability checks do not prove native
queue delivery to an isolated live process. Record actual delivery separately,
both during bootstrap and after the target has a native thread.

The scoped same-workspace two-pane check launched both Codex sessions with
`--no-daemon`; each reported its own pane environment, and both explicitly ACKed
their initial handoffs. The worker independently matched its tool context to
Herdr. The validation session's read-only sandbox denied Herdr socket queries
with `PermissionDenied` / `Operation not permitted`; its reverse queue attempt
failed with `Read-only file system (os error 30)`. Resuming that session with
normal automatic approval still exposed no escalation tool and the queries
remained denied. The validator then independently compared its own allowlisted
tool environment and Git root/common-dir/branch with fresh dispatcher-saved
Herdr CLI responses: all fields matched. The worker's own tool environment
still matched its distinct pane afterward. That initial run verified only
same-workspace identity, not repaired socket access or cross-workspace isolation.
Expanding permissions requires an
authorized route, not invented context or bypassing a denial.
A minimal native queue probe after the resumed bootstrap received an explicit
event-specific ACK in the intended validation pane. Thus forward queue receipt
was demonstrated for that run; the reverse permission failure and the identity
comparison remain separate. An earlier larger queued probe appeared
in that pane but produced no response before a bounded wait timed out; it was
interrupted through Herdr and its fallback received an ACK. Do not infer that
`--no-daemon` universally prevents queue delivery from that incomplete turn.

A later authorized check used two `--no-daemon` Codex sessions in distinct Herdr
workspaces sharing one checkout. Both independently matched their tool identities
to successful live Herdr queries; native queue messages in both directions
received explicit event-specific ACKs. The validator retained the installed
`danger-full-access` with `auto_review` configuration and a source-read-only task
constraint, without permission changes or bypass flags. The coordinator verified
unchanged accepted source and closed only the owned validation workspace after
clean exit. This result does not repair the earlier read-only sandbox failures
or establish separate-checkout or file-access isolation.

The reported historical recovery involved a daemon restart and subsequent
inspection of replacement and still-surviving old processes. It is not standing
authorization to repeat that operation. `shutdown_requested` establishes only
a request; old process exit, corrected tool environment and explicit worker ACK
need their own evidence. Apply the
[workflow's diagnostic and migration boundary](../../skills/shared/issue-workflow/SKILL.md#codex-caller-identity-and-isolation)
to existing sessions; apply supported isolation to new dispatches without
bulk-restarting existing sessions or overwriting downstream adaptations.

## Refresh

Recheck official documentation, installed CLI help and actual available tools
when `refresh_after` applies. Do not probe unrelated live sessions. Preserve an
authorized send's actual result before changing transport; never infer receipt
or completion from a successful submission or an idle notice. Apply the protocol
in [`agent-communication`](../../skills/shared/agent-communication/SKILL.md).
Naming procedure is in [`issue-workflow`](../../skills/shared/issue-workflow/SKILL.md).
