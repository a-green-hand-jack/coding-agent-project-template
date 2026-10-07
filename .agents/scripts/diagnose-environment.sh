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

for product_file in pyproject.toml Dockerfile install.sh .dockerignore; do
  if [[ -f "$product_file" ]]; then
    printf 'ok   optional product file: %s\n' "$product_file"
  else
    printf 'skip optional product file: %s\n' "$product_file"
  fi
done
if [[ -f .dockerignore ]]; then
  for excluded in .agents .project AGENTS.md CLAUDE.md; do
    if grep -Fxq "$excluded" .dockerignore || grep -Fxq "$excluded/" .dockerignore; then
      printf 'ok   docker excludes %s\n' "$excluded"
    else
      printf 'FAIL docker exclusion missing: %s\n' "$excluded"
      fail=1
    fi
  done
fi

if git show-ref --verify --quiet refs/heads/dev || {
  [[ "${GITHUB_ACTIONS:-}" == true ]] &&
  git ls-remote --exit-code --heads origin dev >/dev/null 2>&1
}; then
  printf 'ok   dev branch available\n'
else
  echo 'FAIL local dev branch (run .agents/scripts/init-branches.sh)'; fail=1
fi
if git remote get-url origin >/dev/null 2>&1 && git ls-remote --exit-code --heads origin dev >/dev/null 2>&1; then
  printf 'ok   origin/dev branch\n'
else
  echo 'FAIL origin/dev branch (run .agents/scripts/init-branches.sh)'; fail=1
fi

if command -v gh >/dev/null 2>&1 && repo_view=$(gh repo view --json visibility,nameWithOwner,defaultBranchRef 2>/dev/null); then
  visibility=$(jq -r .visibility <<<"$repo_view")
  default_branch=$(jq -r '.defaultBranchRef.name // "unknown"' <<<"$repo_view")
  printf 'ok   repository visibility: %s\n' "$visibility"
  if [[ "$default_branch" == dev ]]; then
    printf 'ok   GitHub default branch: dev\n'
  else
    printf 'FAIL GitHub default branch: %s (run .agents/scripts/init-branches.sh)\n' "$default_branch"
    fail=1
  fi
else
  echo 'skip repository visibility/default branch (gh unavailable or unauthenticated)'
fi

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

if [[ -f .project/assets.links ]]; then
  while IFS='=' read -r name target; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    if [[ ! -e "assets/$name" ]]; then
      printf 'FAIL missing configured asset link: assets/%s\n' "$name"
      fail=1
    fi
    [[ -e "$target" ]] || { printf 'FAIL missing configured asset target: %s\n' "$target"; fail=1; }
  done < .project/assets.links
fi

exit "$fail"
