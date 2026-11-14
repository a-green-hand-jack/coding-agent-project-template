#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
# The project's Python: AGENTS_PYTHON first, then a virtual environment at
# .project/venv, then python3 on PATH. The same order holds in the other
# inherited commands. Bytecode is never written into the source tree.
python=${AGENTS_PYTHON:-}
if [[ -z "$python" ]]; then
  python=$root/.project/venv/bin/python3
  [[ -x "$python" ]] || python=python3
fi
export PYTHONDONTWRITEBYTECODE=1
exec "$python" -I "$root/.agents/scripts/shared/content_registry.py" --root "$root" "$@"
