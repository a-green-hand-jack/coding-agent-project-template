#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
branch=$(git symbolic-ref --quiet --short HEAD || printf 'detached')
commit=$(git rev-parse HEAD 2>/dev/null || printf 'unborn')
state="$root/.project"

# The primary checkout owns the asset links a new worktree inherits. It is the
# parent of the shared git directory; in the primary checkout there is nothing
# to inherit.
common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
primary=
if [[ "$(basename "$common")" == .git && "$(dirname "$common")" != "$root" ]]; then
  primary=$(dirname "$common")
fi

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

# Create assets/<name> -> <target> unless the entry already exists. $3 says where
# the mapping came from.
link_asset() {
  local name=$1 target=$2 origin=$3 link="assets/$1"
  if [[ -z "$name" || "$name" == */* || "$name" == .* ]]; then
    echo "warning: asset name must be a plain name without '/' or a leading '.', got '$name' ($origin)" >&2
    return 0
  fi
  [[ -e "$link" || -L "$link" ]] && return 0
  [[ -n "$target" ]] || { echo "warning: empty asset target for $name ($origin)" >&2; return 0; }
  [[ -e "$target" ]] || { echo "warning: missing asset target for $name: $target ($origin)" >&2; return 0; }
  ln -s "$target" "$link"
  printf 'linked assets/%s -> %s (%s)\n' "$name" "$target" "$origin"
}

# This worktree's own mappings come first, then the primary checkout's mappings,
# then the links the primary checkout holds under assets/ (made by hand, without
# an assets.links line).
if [[ -f "$state/assets.links" ]]; then
  while IFS='=' read -r name target; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    link_asset "$name" "$target" ".project/assets.links"
  done < "$state/assets.links"
fi
if [[ -n "$primary" ]]; then
  if [[ -f "$primary/.project/assets.links" ]]; then
    while IFS='=' read -r name target; do
      [[ -z "$name" || "$name" == \#* ]] && continue
      link_asset "$name" "$target" "primary checkout's .project/assets.links"
    done < "$primary/.project/assets.links"
  fi
  for entry in "$primary"/assets/*; do
    [[ -L "$entry" ]] || continue
    link_asset "$(basename "$entry")" "$(readlink "$entry")" "primary checkout's assets/"
  done
fi

# Refreshing logins live in the canonical checkout's .project/credentials; a worktree
# links to them and never holds a login of its own (llm-credentials).
if [[ -n "$primary" && -d "$primary/.project/credentials" && ! -e "$state/credentials" && ! -L "$state/credentials" ]]; then
  ln -s "$primary/.project/credentials" "$state/credentials"
  printf 'linked .project/credentials -> canonical checkout\n'
fi

if [[ -x .agents/scripts/setup-project.sh ]]; then
  .agents/scripts/setup-project.sh
fi

printf 'worktree initialized\n  root: %s\n  branch: %s\n  state: %s\n' "$root" "$branch" "$state"
