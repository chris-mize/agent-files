#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec uv run --quiet python -m agent_files.install "$@"
