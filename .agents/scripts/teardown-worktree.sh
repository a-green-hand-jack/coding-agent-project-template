#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == '--migrate-to' && -n "${2:-}" ]] || {
  echo "usage: $0 --migrate-to CANONICAL_PROJECT" >&2
  exit 2
}
root=$(git rev-parse --show-toplevel)
cd "$root"
bash .agents/scripts/inspect-state.sh
bash .agents/scripts/migrate-assets.sh --to "$2"
printf '\nready for managed worktree removal; no source directory was deleted\n'
