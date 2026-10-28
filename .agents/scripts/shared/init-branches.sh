#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
remote=${1:-origin}
branch=${BRANCH_MODEL_BRANCH:-dev}

git remote get-url "$remote" >/dev/null 2>&1 || {
  echo "no '$remote' remote; add one before initializing the branch model" >&2
  exit 1
}

if git show-ref --verify --quiet "refs/heads/$branch"; then
  echo "local branch exists: $branch"
else
  base=$(git symbolic-ref --quiet --short HEAD || printf 'main')
  git show-ref --verify --quiet "refs/heads/$base" || base=main
  git branch "$branch" "$base"
  echo "created local branch: $branch from $base"
fi

if git ls-remote --exit-code --heads "$remote" "$branch" >/dev/null 2>&1; then
  echo "remote branch exists: $remote/$branch"
else
  git push "$remote" "$branch"
  echo "pushed branch: $remote/$branch"
fi

if command -v gh >/dev/null 2>&1; then
  repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
  gh repo edit "$repo" --default-branch "$branch"
  echo "GitHub default branch: $branch"
else
  echo "warning: gh is unavailable; set the GitHub default branch to '$branch'" >&2
fi
