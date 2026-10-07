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
cat <<PROMPT
Work on Issue #$number: $title

Issue: $url
Branch: $branch (create it from dev through Herdr's native worktree command)

Start in the new worktree and run:
  bash .agents/scripts/setup-worktree.sh

Read AGENTS.md, .agents/AGENTS.md, the Issue, and the directly relevant
.agents memory/knowledge/skills before editing. Keep product, development and
human documentation planes separate. Implement the Issue's acceptance criteria,
run the applicable diagnostics and tests, preserve unrelated changes, and
report implementation, validation and remaining risks separately.
PROMPT
