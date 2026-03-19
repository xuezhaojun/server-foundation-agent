#!/usr/bin/env bash
# Sync all submodule repos with shallow clone (depth 1).
# Usage:
#   ./scripts/sync-repos.sh          # init + update all submodules
#   ./scripts/sync-repos.sh --update # update to latest remote commits

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

ACTION="${1:-init}"

case "$ACTION" in
  --update)
    echo "Updating all submodules to latest remote commits (depth 1)..."
    git submodule update --remote --depth 1
    ;;
  *)
    echo "Initializing all submodules (depth 1)..."
    git submodule update --init --depth 1
    ;;
esac

echo "Done. Submodule status:"
git submodule status
