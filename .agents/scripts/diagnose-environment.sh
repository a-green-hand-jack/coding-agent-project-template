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

# Git must track the two files above and ignore the worktree-local state. An
# existing repository's .gitignore often ignores .env.* or assets/, so the files
# exist locally but never reach a commit, a fresh clone or CI.
for tracked in .env.example assets/MANIFEST.yaml; do
  if [[ -f "$tracked" ]] && git check-ignore -q -- "$tracked"; then
    printf 'FAIL %s is ignored by Git: %s\n' "$tracked" "$(git check-ignore -v -- "$tracked")"
    case "$tracked" in
      .env.example) echo '     Add `!.env.example` after the `.env.*` rule in .gitignore.' ;;
      *) echo '     Replace an `assets/` rule with `assets/*` followed by `!assets/README.md`, `!assets/MANIFEST.yaml` and `!assets/.gitkeep` (a directory rule cannot be undone by an exception).' ;;
    esac
    fail=1
  fi
done
if [[ -f .project/home ]]; then
  if git check-ignore -q -- .project/home; then
    printf 'ok   .project/home is ignored by Git\n'
  else
    echo 'FAIL .project/home is not ignored by Git: worktree state, including the .project/credentials link, would show as untracked and can be committed'
    echo '     Add `.project/` to .gitignore.'
    fail=1
  fi
fi

registry=.agents/content-registry.yaml
template_version=
[[ ! -f "$registry" ]] || template_version=$(sed -n '/^template:/,/^[^[:space:]]/p' "$registry" | sed -n 's/^  version: *//p' | head -n 1)
if [[ -n "$template_version" ]]; then
  printf 'ok   adopted template version: %s\n' "$template_version"
else
  fail=1
  if [[ ! -f "$registry" ]]; then
    printf 'FAIL %s is missing; adopt the template with .agents/skills/shared/template-adoption/\n' "$registry"
  else
    if grep -q '^template:' "$registry"; then
      printf 'FAIL adopted template version is not recorded: `template:` in %s has no `version:` line\n' "$registry"
      echo '     Add `  version: <TAG>` under `template:`, taking <TAG> from the first command below.'
    else
      printf 'FAIL adopted template version is not recorded: %s has no `template:` block\n' "$registry"
      echo '     Repositories adopted before v0.1.5 have none. Backfill it, then rerun this script.'
    fi
    cat <<'HINT'
     1. Read the adopted tag from the adoption commit or the developer docs:
          git log --reverse --format='%h %s' -- .agents/content-registry.yaml
          grep -nE 'v[0-9]+\.[0-9]+\.[0-9]+' DEV.md
     2. With no `template:` block, insert one, replacing <TAG> (for example v0.1.1):
          awk -v tag=<TAG> '/^(default_scope|matching|classes|entries):/ && !done { print "template:"; print "  repository: https://github.com/a-green-hand-jack/coding-agent-project-template"; print "  version: " tag; done = 1 } { print }' .agents/content-registry.yaml > .agents/content-registry.yaml.new && mv .agents/content-registry.yaml.new .agents/content-registry.yaml
     See .agents/skills/shared/template-upgrade/SKILL.md ("Backfill a missing template record").
HINT
  fi
fi

# An adopter writes its adaptations of a shared_with_adaptation skill or memory
# record in a trailing section (template-adoption step 5). The template
# repository itself has none, so only warn in other repositories.
remote_id() { sed -E 's#^[a-z+]+://##; s#^[^@/]*@##; s#^([^/:]+):#\1/#; s#\.git$##; s#/$##' <<<"$1"; }
template_repo=
[[ ! -f "$registry" ]] || template_repo=$(sed -n '/^template:/,/^[^[:space:]]/p' "$registry" | sed -n 's/^  repository: *//p' | head -n 1)
origin_url=$(git remote get-url origin 2>/dev/null || true)
if [[ -z "$template_repo" ]]; then
  :
elif [[ -n "$origin_url" && "$(remote_id "$origin_url")" == "$(remote_id "$template_repo")" ]]; then
  echo 'skip adaptation sections (template repository)'
else
  while IFS= read -r entry; do
    file=$entry
    [[ "$entry" == */ ]] && file=${entry}SKILL.md
    [[ -f "$file" ]] || continue
    if grep -qxF '## In this repository' "$file"; then
      printf 'ok   adaptation section: %s\n' "$file"
    else
      printf 'warn adaptation section missing: %s (end it with `## In this repository`; see template-adoption step 5)\n' "$file"
    fi
  done < <(awk '/^  - path: / { p = $3 } /^    scope: shared_with_adaptation$/ && (p ~ /^\.agents\/skills\/.+\/$/ || p ~ /^\.agents\/memory\/.+\.md$/) { print p }' "$registry")
fi

# Only a derived template records the template it follows, in template.upstream
# (DEV.md, template relationship); a project made from it records only it.
upstream_block=
[[ ! -f "$registry" ]] || upstream_block=$(sed -n '/^template:/,/^[^[:space:]]/p' "$registry" |
  awk '/^  upstream:/ { u = 1; print; next } u && /^    / { print; next } u && /^  [^ #]/ { exit }')
if [[ -n "$upstream_block" ]]; then
  upstream_repo=$(sed -n 's/^    repository: *//p' <<<"$upstream_block" | head -n 1)
  upstream_version=$(sed -n 's/^    version: *//p' <<<"$upstream_block" | head -n 1)
  if [[ -n "$upstream_repo" && -n "$upstream_version" ]]; then
    printf 'ok   upstream template: %s %s\n' "$upstream_repo" "$upstream_version"
  else
    printf 'FAIL template.upstream in %s needs `repository:` and `version:` lines, indented four spaces\n' "$registry"
    fail=1
  fi
  if [[ -n "$origin_url" && -n "$template_repo" && "$(remote_id "$origin_url")" != "$(remote_id "$template_repo")" ]]; then
    printf 'warn %s has template.upstream but origin is not %s: a project made from a derived template records only that template; remove the `upstream:` block\n' "$registry" "$template_repo"
  fi
fi

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

# A linked worktree also inherits the primary checkout's link mappings, which
# setup-worktree.sh creates.
links_files=(.project/assets.links)
common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
if [[ "$(basename "$common")" == .git && "$(dirname "$common")" != "$root" ]]; then
  links_files+=("$(dirname "$common")/.project/assets.links")
fi
for links_file in "${links_files[@]}"; do
  [[ -f "$links_file" ]] || continue
  while IFS='=' read -r name target; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    if [[ ! -e "assets/$name" ]]; then
      printf 'FAIL missing configured asset link: assets/%s (run setup-worktree.sh)\n' "$name"
      fail=1
    fi
    [[ -e "$target" ]] || { printf 'FAIL missing configured asset target: %s\n' "$target"; fail=1; }
  done < "$links_file"
done

exit "$fail"
