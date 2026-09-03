#!/usr/bin/env bash
set -euo pipefail

cd "${BASH_SOURCE[0]%/*}"
exec ./install.sh
