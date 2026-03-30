#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found in PATH."
  exit 1
fi

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

unset ALL_PROXY HTTP_PROXY HTTPS_PROXY NO_PROXY all_proxy http_proxy https_proxy no_proxy

UNTIL_DATE="${1:-2026-03-29}"
SOURCES="${2:-}"

uv sync --extra dev

if [[ -n "$SOURCES" ]]; then
  exec uv run python -m src.backfill --until "$UNTIL_DATE" --sources "$SOURCES"
fi

exec uv run python -m src.backfill --until "$UNTIL_DATE"
