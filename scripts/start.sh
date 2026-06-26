#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  echo "Virtualenv not found at $ROOT_DIR/.venv"
  echo "Create one with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"

exec python -m southnotary_uploader "$@"
