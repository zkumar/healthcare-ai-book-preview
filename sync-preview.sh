#!/usr/bin/env bash
# Sync selected chapters from the PRIVATE book repo into this PUBLIC preview repo,
# then build + deploy the MkDocs site to GitHub Pages.
#
# Source of truth:  ~/Documents/Claude/Projects/healthcare-ai-book   (private)
# Published subset:  this repo                                        (public)
#
# Usage:
#   ./sync-preview.sh           # sync chapters + rebuild nav (no deploy)
#   ./sync-preview.sh --deploy  # sync + deploy to GitHub Pages
set -euo pipefail

PRIVATE="$HOME/Documents/Claude/Projects/healthcare-ai-book"
PUBLIC="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(cat "$PRIVATE/graphify-out/.graphify_python" 2>/dev/null || echo python3)"

if [ ! -d "$PRIVATE/chapters" ]; then
    echo "error: private repo not found at $PRIVATE" >&2
    exit 1
fi

echo "Syncing preview chapters from private repo..."
"$PYTHON" "$PUBLIC/sync_preview.py" "$PRIVATE" "$PUBLIC"

if [ "${1:-}" = "--deploy" ]; then
    echo
    echo "Deploying to GitHub Pages..."
    cd "$PUBLIC"
    mkdocs gh-deploy --clean --message "Deploy preview {sha} via sync-preview.sh"
    echo
    echo "Live at: https://zkumar.github.io/healthcare-ai-book-preview/"
else
    echo
    echo "Synced. Preview locally with:  mkdocs serve"
    echo "Deploy with:                   ./sync-preview.sh --deploy"
fi
