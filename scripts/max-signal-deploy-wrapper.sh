#!/bin/bash
# Wrapper script for max-signal-deploy
# This script should be installed at /usr/local/bin/max-signal-deploy
# It always calls the latest version from the git repository

set -e

# Project root (adjust if your deployment is in a different location)
PROJECT_ROOT="/srv/max-signal"
DEPLOY_SCRIPT="${PROJECT_ROOT}/scripts/deploy.sh"

# Check if project directory exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Project directory not found: $PROJECT_ROOT"
    echo "   Please ensure the project is cloned to $PROJECT_ROOT"
    exit 1
fi

# Check if deploy script exists
if [ ! -f "$DEPLOY_SCRIPT" ]; then
    echo "❌ Deploy script not found: $DEPLOY_SCRIPT"
    echo "   Please ensure the project is properly cloned"
    exit 1
fi

# Change to project root and execute the script
cd "$PROJECT_ROOT"
exec "$DEPLOY_SCRIPT" "$@"

