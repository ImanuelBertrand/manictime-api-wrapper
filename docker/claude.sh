#!/bin/bash
set -e

if ! command -v claude &>/dev/null; then
    echo "Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash
fi

exec claude --dangerously-skip-permissions "$@"
