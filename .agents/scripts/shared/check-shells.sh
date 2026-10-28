#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
count=0
while IFS= read -r -d '' file; do
  bash -n "$file"
  count=$((count + 1))
done < <(find "$root/.agents" -type f -name '*.sh' -print0)
printf 'shell syntax: PASS (%s files, recursive)\n' "$count"
