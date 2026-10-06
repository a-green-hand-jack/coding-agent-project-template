#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
branch=$(git symbolic-ref --quiet --short HEAD || printf 'detached')
commit=$(git rev-parse HEAD 2>/dev/null || printf 'unborn')
state="$root/.project"

mkdir -p "$state"/{state,runs,artifacts,manifest}
printf '%s\n' "$root" > "$state/home"
{
  printf 'PROJECT_ROOT=%q\n' "$root"
  printf 'PROJECT_BRANCH=%q\n' "$branch"
  printf 'PROJECT_COMMIT=%q\n' "$commit"
  printf 'PROJECT_STATE=%q\n' "$state"
} > "$state/worktree.env"

[[ -f .env.example ]] || echo 'warning: .env.example is missing' >&2
[[ -f assets/MANIFEST.yaml ]] || echo 'warning: assets/MANIFEST.yaml is missing' >&2

if [[ -x .agents/scripts/setup-project.sh ]]; then
  .agents/scripts/setup-project.sh
fi

printf 'worktree initialized\n  root: %s\n  branch: %s\n  state: %s\n' "$root" "$branch" "$state"
