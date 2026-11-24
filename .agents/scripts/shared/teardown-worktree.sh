#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == '--migrate-to' && -n "${2:-}" ]] || {
  echo "usage: $0 --migrate-to CANONICAL_PROJECT [--also NAME]... [--skip NAME=REASON]..." >&2
  exit 2
}
root=$(git rev-parse --show-toplevel)
cd "$root"
destination=$2
shift 2
# The project's own preconditions (a stopped service, a released checkout) run
# before anything is inspected or copied; a non-zero exit stops the teardown
# with nothing migrated. The template never stops a process itself.
if [[ -x .agents/scripts/project/teardown-project.sh ]]; then
  .agents/scripts/project/teardown-project.sh || {
    printf 'teardown-project.sh stopped the teardown; nothing was migrated\n' >&2
    exit 1
  }
fi
bash .agents/scripts/shared/inspect-state.sh
bash .agents/scripts/shared/migrate-assets.sh --to "$destination" "$@"
printf '\nready for managed worktree removal; no source directory was deleted\n'
