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

if [[ "${SKIP_BRANCH_INIT:-0}" != 1 && "${CI:-}" != true && "${GITHUB_ACTIONS:-}" != true && "$branch" == main ]]; then
  if [[ -x .agents/scripts/init-branches.sh ]]; then
    .agents/scripts/init-branches.sh || echo 'warning: branch model initialization needs attention' >&2
  fi
fi

[[ -f .env.example ]] || echo 'warning: .env.example is missing' >&2
[[ -f assets/MANIFEST.yaml ]] || echo 'warning: assets/MANIFEST.yaml is missing' >&2

if [[ -f "$state/assets.links" ]]; then
  while IFS='=' read -r name target; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    [[ -n "$target" ]] || { echo "warning: empty asset target for $name" >&2; continue; }
    [[ -e "$target" ]] || { echo "warning: missing asset target for $name: $target" >&2; continue; }
    link="assets/$name"
    [[ -e "$link" || -L "$link" ]] && continue
    ln -s "$target" "$link"
  done < "$state/assets.links"
fi

if [[ -x .agents/scripts/setup-project.sh ]]; then
  .agents/scripts/setup-project.sh
fi

printf 'worktree initialized\n  root: %s\n  branch: %s\n  state: %s\n' "$root" "$branch" "$state"
