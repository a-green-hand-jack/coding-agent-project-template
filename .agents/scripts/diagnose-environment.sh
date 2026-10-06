#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
fail=0
check() {
  if "$@" >/dev/null 2>&1; then printf 'ok   %s\n' "$*"; else printf 'FAIL %s\n' "$*"; fail=1; fi
}

check git --version
check bash --version
[[ -d .agents ]] && printf 'ok   .agents directory\n' || { echo 'FAIL .agents directory'; fail=1; }
[[ -f .env.example ]] && printf 'ok   .env.example\n' || { echo 'FAIL .env.example'; fail=1; }
[[ -f assets/MANIFEST.yaml ]] && printf 'ok   assets manifest\n' || { echo 'FAIL assets manifest'; fail=1; }

if [[ -f .project/home ]]; then
  expected=$(cat .project/home)
  [[ "$expected" == "$root" ]] && printf 'ok   worktree marker\n' || { echo 'FAIL worktree marker'; fail=1; }
else
  echo 'FAIL .project/home (run setup-worktree.sh)'
  fail=1
fi

while IFS= read -r -d '' link; do
  if [[ ! -e "$link" ]]; then
    printf 'FAIL broken asset link: %s\n' "$link"
    fail=1
  fi
done < <(find assets -type l -print0 2>/dev/null)

exit "$fail"
