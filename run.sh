#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d .venv ]; then
  echo "Virtual environment not found. Run: python -m venv .venv"
  exit 1
fi

source .venv/bin/activate

if [ "$#" -eq 0 ]; then
  python main.py --help
  exit 0
fi

python main.py "$@"
