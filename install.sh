#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python -m agent_files.install "$@"
