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
bash .agents/scripts/inspect-state.sh
bash .agents/scripts/migrate-assets.sh --to "$destination" "$@"
printf '\nready for managed worktree removal; no source directory was deleted\n'
