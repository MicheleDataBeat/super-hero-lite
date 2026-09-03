#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  printf 'Usage: scripts/manifest.sh --write|--verify\n' >&2
}

if [[ "$#" -ne 1 ]]; then
  usage
  exit 2
fi

case "$1" in
  --write | --verify) ;;
  *)
    usage
    exit 2
    ;;
esac

# The manifest rule has one implementation. This entry point only names it, so
# a Host without find, sort and shasum verifies the same file set and digests.
exec python3 -B "$PACKAGE_DIR/scripts/manifest.py" "$1"
