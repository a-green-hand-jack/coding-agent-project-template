#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONDONTWRITEBYTECODE=1
exec "${AGENTS_PYTHON:-python3}" -I "$root/.agents/scripts/shared/content_registry.py" --root "$root" "$@"
