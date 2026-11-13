#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
exec "${AGENTS_PYTHON:-python3}" -I -B "$root/.agents/scripts/shared/content_registry.py" --root "$root" "$@"
