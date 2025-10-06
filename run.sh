#!/usr/bin/env bash
# ePaper project launcher script
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_LEVEL="INFO"
VENV_PATH=""
usage(){ cat <<'USAGE'
Usage: ./run.sh [options]
  -v, --venv <path>   Activate virtual environment
  -q, --quiet         Set log level WARNING
  -d, --debug         Set log level DEBUG
  -h, --help          Help
USAGE
}
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0;;
    -q|--quiet) LOG_LEVEL="WARNING"; shift;;
    -d|--debug) LOG_LEVEL="DEBUG"; shift;;
    -v|--venv) [[ $# -ge 2 ]] || { echo "--venv needs path" >&2; exit 1; }; VENV_PATH="$2"; shift 2;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done
if [[ -n "$VENV_PATH" && -f "$VENV_PATH/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_PATH/bin/activate"
fi
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
echo "Starting ePaper (log: $LOG_LEVEL)"
exec python - <<PY
import logging
from src import main as ep_main
logging.getLogger().setLevel(getattr(logging, "${LOG_LEVEL}", logging.INFO))
ep_main.main()
PY