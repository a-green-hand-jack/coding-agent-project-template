#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
echo '## repository'
printf 'root: %s\n' "$root"
printf 'branch: %s\n' "$(git symbolic-ref --quiet --short HEAD || echo detached)"
echo
echo '## git status (including ignored state)'
git status --short --ignored
echo
echo '## project state'
if [[ -d .project ]]; then
  du -sh .project 2>/dev/null || true
  find .project -maxdepth 2 -type f -print | sort
else
  echo '.project does not exist; run setup-worktree.sh'
fi
echo
echo '## assets'
find assets -maxdepth 1 -type l -printf '%f -> %l\n' 2>/dev/null || true
