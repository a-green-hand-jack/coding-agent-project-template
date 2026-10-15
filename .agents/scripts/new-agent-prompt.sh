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
[[ -n "$branch" ]] || branch="fix/issue-$number"
# The working rules mirror "Issue session rules" in the issue-workflow skill.
cat <<PROMPT
Work on Issue #$number: $title

Issue: $url
Branch: $branch (create it from dev through Herdr's native worktree command)

Start in the new worktree and run:
  bash .agents/scripts/setup-worktree.sh

Read AGENTS.md, .agents/AGENTS.md, the Issue, and the directly relevant
.agents memory/knowledge/skills before editing. Keep product, development and
human documentation planes separate, and preserve unrelated changes.

Working rules for this session:
- Verify to completion. Run every check the Issue's acceptance and the
  project's CI call for, including real runs and, after a push, gh pr checks.
  Report one definite result with the commands and their output. Name only a
  step the maintainer alone can perform (an interactive login, a decision) as
  a blocker, saying what they must do. Do not add a "not verified" list, and
  never claim a check that was not run.
- Fix what you meet. A defect met on the way that blocks this Issue or is
  related to it is fixed here, verified and listed in the PR; that is part of
  the Issue, not an unrequested feature. Only an unrelated, larger problem is
  reported for a separate Issue.
- Other worktrees are not your concern. Parallel worktrees may change the same
  files; the dev checkout resolves conflicts when it merges the PRs. Complete
  the Issue fully and do not narrow the change to avoid conflicts.
- Merge implies close-out. Approval to merge the PR covers its close-out: right
  after the verified merge the coordinating session migrates .project/ and
  removes this worktree without asking again, so archive results that cannot
  be rebuilt before the merge.
PROMPT
