#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/src/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found in PATH."
  echo "Install Node.js first, then rerun this script."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing in $FRONTEND_DIR/node_modules."
  echo "Run 'cd mneme/src/frontend && npm install' first."
  exit 1
fi

cd "$FRONTEND_DIR"

echo "Starting Vite on http://127.0.0.1:5173"
exec npm run dev -- --host 127.0.0.1 --port 5173
