#!/usr/bin/env bash
set -euo pipefail

usage() { echo "usage: $0 --to CANONICAL_PROJECT" >&2; exit 2; }
[[ "${1:-}" == '--to' && -n "${2:-}" ]] || usage
destination=$(realpath -m "$2")
root=$(git rev-parse --show-toplevel)
cd "$root"
[[ "$destination" != "$root" && "$destination" != "$root"/* ]] || { echo 'destination must be outside this worktree' >&2; exit 1; }
mkdir -p "$destination/.project/migrations"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
migration="$destination/.project/migrations/$(basename "$root")-$stamp"
mkdir -p "$migration"
for name in state runs artifacts manifest; do
  [[ -e ".project/$name" ]] && cp -a ".project/$name" "$migration/"
done
mkdir -p "$destination/assets"
for entry in assets/* assets/.[!.]*; do
  [[ -e "$entry" || -L "$entry" ]] || continue
  # Tracked files and links reach the destination through Git, not migration.
  if git --literal-pathspecs ls-files --error-unmatch -- "$entry" >/dev/null 2>&1; then
    continue
  fi
  name=${entry#assets/}
  target="$destination/assets/$name"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ -L "$entry" && -L "$target" && "$(readlink "$entry")" == "$(readlink "$target")" ]]; then
      continue
    fi
    echo "refusing to overwrite destination asset: $target" >&2
    exit 1
  fi
  cp -a "$entry" "$target"
done
printf 'migrated_from=%q\n' "$root" > "$migration/migrated-from.env"
printf 'migrated_to=%s\n' "$destination"
printf 'migration=%s\n' "$migration"
printf 'state and asset links copied; source was not deleted\n'
