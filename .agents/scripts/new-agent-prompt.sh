#!/usr/bin/env bash
set -euo pipefail

[[ -n "${1:-}" && $# -le 4 ]] || { echo "usage: $0 ISSUE_NUMBER [BRANCH] [TARGET_BASE] [COORDINATOR_HANDOFF]" >&2; exit 2; }
issue=$1
branch=${2:-}
target_base=${3:-dev}
coordinator_handoff=${4:-}
if [[ -n "$coordinator_handoff" && ( ! -f "$coordinator_handoff" || ! -r "$coordinator_handoff" || ! -s "$coordinator_handoff" ) ]]; then
  echo 'COORDINATOR_HANDOFF must be a readable, nonempty local file' >&2
  exit 2
fi
if ! command -v gh >/dev/null 2>&1; then
  echo 'gh is required to load the Issue details' >&2
  exit 1
fi
json=$(gh issue view "$issue" --json number,title,body,url)
number=$(jq -r .number <<<"$json")
title=$(jq -r .title <<<"$json")
url=$(jq -r .url <<<"$json")
body=$(jq -r .body <<<"$json")
# The Issue's own dispatch record (issue-workflow, "Dispatch by difficulty").
dispatch=$(printf '%s\n' "$body" | awk '
  /^## Dispatch[[:space:]]*$/ { inside = 1; next }
  inside && /^## / { exit }
  inside && $0 !~ /^[[:space:]]*$/ { started = 1 }
  inside && started { print }
')
[[ -n "$branch" ]] || branch="fix/issue-$number"
# The project's declared writing conventions (issue-workflow, "Writing conventions").
registry="$(git rev-parse --show-toplevel)/.agents/content-registry.yaml"
writing=
[[ ! -f "$registry" ]] || writing=$(sed -n '/^writing:/,/^[^[:space:]]/p' "$registry")
language=$(sed -n 's/^  language: *//p' <<<"$writing" | head -n 1)
sections=$(sed -n 's/^  issue_sections: *//p' <<<"$writing" | head -n 1)
# The working rules mirror "Issue session rules" in the issue-workflow skill.
cat <<PROMPT
Work on Issue #$number: $title

Issue: $url
Branch: $branch (create it from $target_base through Herdr's native worktree command)
PR target: $target_base (a parent integration target must be declared in the Issue)

Start in the new worktree and run:
  bash .agents/scripts/setup-worktree.sh

Read AGENTS.md, .agents/AGENTS.md, the Issue, and the directly relevant
.agents memory/knowledge/skills before editing. Read
.agents/skills/shared/agent-communication/SKILL.md before sending or
receiving a handoff. Keep product, development and human documentation planes
separate, and preserve unrelated changes.

Confirm the handoff's identity mapping: stable project-issue-number task key,
role and attempt; returned workspace/tab/pane IDs and actual labels; Herdr agent
name and native session/thread ID. Align names where supported, keep Herdr's
returned worktree path, and record an ID mapping when native naming is unavailable.
Validate each complete Herdr agent name, including role/attempt suffix, against
[a-z][a-z0-9_-]{0,31} (32 characters maximum) and live uniqueness before start/rename.
Do not invent naming flags or rename sessions outside this Issue.

Working rules for this session:
- Before implementation, apply issue-workflow's Codex caller identity and
  isolation check. Compare your own allowlisted HERDR identity variables,
  repository/common Git dir and native thread with Herdr-returned identities;
  record actual startup mode/model/provider/effort, then explicitly ACK scope.
  For applicable Codex dispatches verify supported --no-daemon isolation.
  Missing/stale context permits only authorized read-only diagnosis until
  resolved; never fake variables or restart shared services as a default fix.
  Missing native thread permits only the preflighted communication fallback;
  test actual queue receipt separately, including after bootstrap. Startup,
  corrected environment, submitted message and receiver ACK are distinct facts.
- Before the first agent run, inspect every Herdr hook that will run (including
  SessionStart) and record a per-hook receipt under .project/state/. Approve
  only known, necessary hooks; stop on an unknown, changed, or uninspectable
  hook and report its exact name and evidence. Never blanket-approve or
  blanket-reject hooks.
- Verify to completion. Run every check the Issue's acceptance and the
  project's local check (DEV.md) call for, including real runs. After a push you
  may read gh pr checks and report its state (passed, failed or not run), but do
  not wait for it and do not stop because CI did not run; the local result is
  the evidence. Report one definite result with the commands and their output. Name only a
  step the maintainer alone can perform (an interactive login, a decision) as
  a blocker, saying what they must do. Do not add a "not verified" list, and
  never claim a check that was not run.
- Keep real runs small and sufficient. Before a real run, judge whether the
  change can affect something the system must keep doing; a change the
  regression checks already cover needs no real run. A run that is needed uses
  the smallest task, the fewest components and a small budget to prove this
  change, reuses evidence that already answers the question, and avoids the
  most expensive providers unless the change concerns them. The plan and the PR
  name each run's agent, provider, model and effort, what it proves and why it
  must run. This does not relax "Verify to completion": every check the
  acceptance calls for still runs.
- Route cost first. Ordinary tests, regression checks, documentation and
  mechanical work use the cheapest token source and the cheapest model that can
  judge them; an expensive provider or model is used only when the change
  concerns its request format, permissions, capability or real behavior, and the
  plan says why. A cheap run is still a real provider-backed run and never
  stands in for the capability the acceptance must prove. A change of agent,
  provider, model or effort is recorded as a re-dispatch in the Issue's Dispatch
  section.
- Fix what you meet. A defect met on the way that blocks this Issue or is
  related to it is fixed here, verified and listed in the PR; that is part of
  the Issue, not an unrequested feature. Only an unrelated, larger problem is
  reported for a separate Issue.
- Other worktrees are not your concern. Parallel worktrees may change the same
  files; at merge the coordinator that claimed this Issue resolves conflicts
  with the current $target_base in this worktree, itself or through you. Complete the
  Issue fully and do not narrow the change to avoid conflicts.
- Merge implies close-out. Approval to merge the PR covers its close-out: after
  the verified merge, reconcile background acceptance, pending audits and
  promised follow-ups. Keep this worktree while it still owns those duties,
  or explicitly transfer them under authorization with acknowledgement. Then
  migrate .project/ and remove it without asking again. Archive results that
  cannot be rebuilt before the merge. A child integration merge does not
  complete the parent's final delivery to dev.
- Keep your own working files (plans, PR body drafts and messages to the
  coordinator) in .project/state/, not in the root of .project/. Close-out
  copies .project/state/ without further rules; a file in the root of
  .project/ that no migration rule covers stops the migration.
- For every handoff or follow-up, preflight the target session and input line,
  choose the native transport from .agents/skills/shared/agent-communication/SKILL.md,
  and record the transport, target session/thread and confirmation result. A
  successful pane write alone is not receipt confirmation; after a stall,
  inspect status and preserve the exact evidence before retrying.
- ACK this handoff's scope and reporting authorization before implementation.
  Proactively send implementation/acceptance results, PR-created, head-updated,
  blockers or acceptance failures, and responsibility/close-out changes to the
  claiming coordinator before ending the affected turn. Each event carries an
  event ID, task/role/attempt, Issue/PR (or none), exact head/run (or base plus
  saved diff for uncommitted work), evidence, pending duties/owners and requested
  action. Follow issue-workflow's delivery reporting and agent-communication's
  receipt/recovery rules; a local final reply or idle state is not receipt.
  Record submitted and explicit ACK separately. Missing ACK stays pending with
  an owner, recovery entry and bounded retry/next checkpoint. On resume check
  prior receipts and the current/terminal summary before necessary GitHub checks;
  duplicates or old heads never replace
  current acceptance. Without delivery authorization report ready-for-review
  and wait; notifications grant no commit/push/PR/merge/release permission.
- Protect acceptance inputs using issue-workflow's Acceptance write
  responsibility section. Before either session tests a shared checkout, record
  the exact version (including uncommitted inputs), owner, writers, protected
  paths and allowed outputs. Require explicit pause ACKs before starting and
  explicit return before resuming writes. New edits, drift, restart or timeout
  never silently release responsibility; end/invalidate and stop or isolate the
  old run before transfer. An independently immutable snapshot records its
  provenance and isolation instead of freezing the development checkout.
- Apply agent-communication's message cadence: critical handoffs, failures and
  changes affecting the receiver's next action go promptly; combine results at
  the same checkpoint/version, and keep routine progress local. ACKs need no
  ACK; return a duplicate receipt only for a still-pending confirmation duty.
  Keep independent work moving; no fixed-time polling or heartbeats. Pending
  handoffs block their dependent actions, not unrelated work.
- Classify received backlog before queries, replies or dispatch using
  agent-communication's receive-time classification. Recover the current or
  migrated terminal summary and fold already-delivered duplicates, superseded
  milestones and terminal no-new-information events locally: zero new GitHub
  queries, dispatches, tests, messages/ACKs or user completion reports. Different
  event IDs can cover the same outcome. Retain conflicting same-ID content,
  late risks and untransferred duties with owners; reconcile each actual increment
  once. Genuine new user instructions are not events to deduplicate; old event
  authorization is not fresh approval. Preserve the summary/evidence through
  migration, add no waiting window or consumer, and record forced client replies
  as runtime limits rather than claiming the underlying queue was changed.
- Use .agents/skills/shared/development-writing/SKILL.md for Issues, PRs,
  comments and commit messages. Keep current bodies aligned with agreed scope
  and final behavior; retain important decisions in comments and identify the
  head/run behind evidence. Writing guidance never authorizes sending or committing.
PROMPT
if [[ -n "$language" ]]; then
  cat <<PROMPT
- Write Issues, PRs, comments and human documents in $language (the
  registry's writing block). Text the template ships, above an "In this
  repository" section or printed by its scripts, keeps its language.
PROMPT
  [[ -z "$sections" ]] || printf '  An Issue body starts with: %s.\n' "$sections"
  printf '  Commit messages use %s unless development-writing has a project-specific override.\n' "$language"
fi
if [[ -n "$coordinator_handoff" ]]; then
  printf '\nLocal coordinator mapping and reporting boundary:\n\n'
  cat -- "$coordinator_handoff"
  printf '\n'
else
  cat <<'PROMPT'

Before dispatch, append the local coordinator mapping and reporting boundary:
claimant name from Dispatch; resolved pane and native session/thread (or the
unresolved-address reason and conditional fallback); task/role/attempt;
authorized contact/events and delivery constraints; pending owner, recovery
entry, bounded retry/next checkpoint and permitted escalation route.
Keep machine-private addresses in .project/state/, not public Issue/PR text.
Do not infer cross-session authorization from discovering a coordinator name.
PROMPT
fi
if [[ -n "$dispatch" ]]; then
  cat <<PROMPT

The Issue's Dispatch section records the agent, provider, model and effort this
session runs with. Read it before the first run, and append a re-dispatched line
there whenever any of them changes:

$dispatch
PROMPT
else
  cat <<PROMPT

The Issue has no Dispatch section yet. Before the first run, record the agent,
provider, model and effort there, and append a re-dispatched line whenever any
of them changes.
PROMPT
fi
