#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-package}"
export PYTHONDONTWRITEBYTECODE=1
FAIL=0
WARN=0

pass(){ printf 'PASS  %s\n' "$*"; }
fail(){ printf 'FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
run_check(){
  local label="$1"
  shift
  if "$@"; then
    pass "$label"
  else
    fail "$label"
  fi
}

if [[ "$MODE" != "package" ]]; then
  printf 'Usage: %s\n' "${BASH_SOURCE[0]}" >&2
  exit 2
fi

cd "$PACKAGE_DIR"
run_check "upstream compatibility" python3 -m unittest evals/test_compatibility.py -v
run_check "skill packages" python3 -m unittest evals/test_skill_packages.py -v
run_check "removed architecture" python3 -m unittest evals/test_removed_architecture.py -v
run_check "Codex lifecycle" python3 -m unittest distributions/codex/evals/test_lifecycle.py -v
run_check "Claude Code lifecycle" python3 -m unittest distributions/claude-code/evals/test_lifecycle.py -v
run_check "Claude Code plugin" python3 -m unittest evals/test_claude_code_plugin.py -v
run_check "repository contract" python3 -m unittest evals/test_repository_contract.py -v
run_check "shell syntax" find . -type f \( -name '*.sh' -o -name '*.command' \) \
  -not -path './.git/*' -exec sh -c \
  'status=0; for file do bash -n "$file" || status=1; done; exit "$status"' \
  sh {} +
run_check "package manifest" bash scripts/manifest.sh --verify

printf '\nValidation summary: %d failure(s), %d warning(s).\n' "$FAIL" "$WARN"
[[ "$FAIL" -eq 0 ]]
