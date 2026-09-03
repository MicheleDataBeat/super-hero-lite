#!/usr/bin/env bash
set -euo pipefail

DISTRIBUTION_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
PACKAGE_ROOT="$(cd "$DISTRIBUTION_DIR/../.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PYTHONDONTWRITEBYTECODE=1

if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: missing required command: python3\n' >&2
  exit 1
fi

python3 -B "$DISTRIBUTION_DIR/lib/managed_state.py" uninstall \
  --package-root "$PACKAGE_ROOT" \
  --home "$HOME" \
  --codex-home "$CODEX_HOME"
