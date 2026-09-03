#!/usr/bin/env bash
set -euo pipefail

DISTRIBUTION_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
PACKAGE_ROOT="$(cd "$DISTRIBUTION_DIR/../.." && pwd)"
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
export PYTHONDONTWRITEBYTECODE=1

case "${1:-}" in
  "")
    VALIDATE_MODE=installed
    ;;
  --package)
    VALIDATE_MODE=package
    ;;
  *)
    printf 'Usage: %s [--package]\n' "${BASH_SOURCE[0]}" >&2
    exit 2
    ;;
esac

if [[ "$VALIDATE_MODE" == package ]]; then
  python3 -B "$DISTRIBUTION_DIR/lib/managed_state.py" validate \
    --package-root "$PACKAGE_ROOT" \
    --home "$HOME" \
    --claude-home "$CLAUDE_CONFIG_DIR" \
    --package
else
  python3 -B "$DISTRIBUTION_DIR/lib/managed_state.py" validate \
    --package-root "$PACKAGE_ROOT" \
    --home "$HOME" \
    --claude-home "$CLAUDE_CONFIG_DIR"
fi
