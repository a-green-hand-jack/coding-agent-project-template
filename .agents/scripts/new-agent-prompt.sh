#!/usr/bin/env bash
set -euo pipefail

[[ -n "${1:-}" ]] || { echo "usage: $0 ISSUE_NUMBER [BRANCH]" >&2; exit 2; }
issue=$1
branch=${2:-}
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
Branch: $branch (create it from dev through Herdr's native worktree command)

Start in the new worktree and run:
  bash .agents/scripts/setup-worktree.sh

Read AGENTS.md, .agents/AGENTS.md, the Issue, and the directly relevant
.agents memory/knowledge/skills before editing. Read
.agents/skills/shared/agent-communication/SKILL.md before sending or
receiving a handoff. Keep product, development and human documentation planes
separate, and preserve unrelated changes.

Working rules for this session:
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
  with the current dev in this worktree, itself or through you. Complete the
  Issue fully and do not narrow the change to avoid conflicts.
- Merge implies close-out. Approval to merge the PR covers its close-out: right
  after the verified merge the coordinator migrates .project/ and removes this
  worktree without asking again, so archive results that cannot be rebuilt
  before the merge.
- Keep your own working files (plans, PR body drafts and messages to the
  coordinator) in .project/state/, not in the root of .project/. Close-out
  copies .project/state/ without further rules; a file in the root of
  .project/ that no migration rule covers stops the migration.
- For every handoff or follow-up, preflight the target session and input line,
  choose the native transport from .agents/skills/shared/agent-communication/SKILL.md,
  and record the transport, target session/thread and confirmation result. A
  successful pane write alone is not receipt confirmation; after a stall,
  inspect status and preserve the exact evidence before retrying.
PROMPT
if [[ -n "$language" ]]; then
  cat <<PROMPT
- Write Issues, PRs, comments and human documents in $language (the
  registry's writing block). Text the template ships, above an "In this
  repository" section or printed by its scripts, keeps its language.
PROMPT
  [[ -z "$sections" ]] || printf '  An Issue body starts with: %s.\n' "$sections"
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
