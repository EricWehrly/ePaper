#!/usr/bin/env bash
# Test runner for ePaper project
set -euo pipefail

# Run tests in Docker container with proper environment
# Mount test directory and exclude playwright integration tests
exec sudo docker compose run --rm \
  -v "$(pwd)/test:/app/test:ro" \
  epaper-display \
  python -m pytest test/ --ignore=test/integration --ignore=test/playwright "$@"
