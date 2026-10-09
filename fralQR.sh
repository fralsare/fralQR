#!/usr/bin/env bash
# fralQR launcher (Linux). Just double-click me (right-click > Open as Text,
# make executable once with: chmod +x fralQR.sh) or run: ./fralQR.sh
set -euo pipefail
cd "$(dirname "$0")"
exec python3 fralQR.py "$@"
