#!/usr/bin/env bash
# Simple launcher for ePaper project
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Optionally activate a virtualenv if provided as first argument
# Usage examples:
#   ./run.sh                 -> runs with system python
#   ./run.sh /path/to/venv   -> activates venv and runs
# Any additional arguments are forwarded to python -m src.main

VENV_PATH=""
if [[ $# -ge 1 && -d "$1" && -f "$1/bin/activate" ]]; then
  VENV_PATH="$1"
  shift
fi

if [[ -n "$VENV_PATH" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
  echo "Activated virtualenv: $VENV_PATH"
fi

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

echo "Starting ePaper - forwarding args to python -m src.main"
echo "PYTHONPATH=$PYTHONPATH"

# Run the main module, forwarding all remaining arguments
exec python -m src.main "$@"