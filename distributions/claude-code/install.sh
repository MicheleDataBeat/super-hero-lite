#!/usr/bin/env bash
set -euo pipefail

DISTRIBUTION_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
PACKAGE_ROOT="$(cd "$DISTRIBUTION_DIR/../.." && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
export PYTHONDONTWRITEBYTECODE=1

for required_command in git gh python3 claude; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'ERROR: missing required command: %s\n' "$required_command" >&2
    exit 1
  fi
done

if ! gh auth status >/dev/null 2>&1; then
  printf 'ERROR: GitHub CLI authentication failed: run gh auth login\n' >&2
  exit 1
fi

python3 -B "$DISTRIBUTION_DIR/lib/managed_state.py" install \
  --package-root "$PACKAGE_ROOT" \
  --home "$HOME" \
  --claude-home "$CLAUDE_CONFIG_DIR"
