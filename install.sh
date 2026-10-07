#!/usr/bin/env bash
set -euo pipefail

# Replace this entrypoint with the product's supported installation policy.
python_bin=${PYTHON:-python3}
read -r -a pip_args <<< "${PIP_INSTALL_ARGS:-}"
exec "$python_bin" -m pip install "${pip_args[@]}" .
