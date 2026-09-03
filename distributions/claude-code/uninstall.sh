#!/usr/bin/env bash
set -euo pipefail

DISTRIBUTION_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
PACKAGE_ROOT="$(cd "$DISTRIBUTION_DIR/../.." && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
export PYTHONDONTWRITEBYTECODE=1

if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: missing required command: python3\n' >&2
  exit 1
fi

python3 -B "$DISTRIBUTION_DIR/lib/managed_state.py" uninstall \
  --package-root "$PACKAGE_ROOT" \
  --home "$HOME" \
  --claude-home "$CLAUDE_CONFIG_DIR"
