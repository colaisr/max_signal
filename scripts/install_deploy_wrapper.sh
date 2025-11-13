#!/bin/bash
# Install max-signal-deploy wrapper to /usr/local/bin
# This ensures the wrapper always calls the latest version from the git repo
# Usage: sudo ./scripts/install_deploy_wrapper.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WRAPPER_SCRIPT="${SCRIPT_DIR}/max-signal-deploy-wrapper.sh"
TARGET="/usr/local/bin/max-signal-deploy"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}📦 Installing max-signal-deploy Wrapper${NC}"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Check if wrapper script exists
if [ ! -f "$WRAPPER_SCRIPT" ]; then
    echo -e "${RED}❌ Wrapper script not found: $WRAPPER_SCRIPT${NC}"
    exit 1
fi

# Check if project root exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Project root not found: $PROJECT_ROOT${NC}"
    echo "   Please ensure the project is cloned to $PROJECT_ROOT"
    exit 1
fi

# Make wrapper executable
chmod +x "$WRAPPER_SCRIPT"

# Check if old script exists
if [ -f "$TARGET" ] && [ ! -L "$TARGET" ]; then
    echo -e "${YELLOW}⚠️  Found existing script at $TARGET${NC}"
    echo "   Backing up to ${TARGET}.backup"
    cp "$TARGET" "${TARGET}.backup"
fi

# Install wrapper (copy, not symlink, so it works even if repo is moved)
echo "📋 Installing wrapper to $TARGET..."
cp "$WRAPPER_SCRIPT" "$TARGET"
chmod +x "$TARGET"

echo ""
echo -e "${GREEN}✅ Wrapper installed successfully!${NC}"
echo ""
echo "📋 Usage:"
echo "   max-signal-deploy"
echo ""
echo "   This will always call the latest version from:"
echo "   ${PROJECT_ROOT}/scripts/deploy.sh"
echo ""
echo "📋 To update the wrapper after pulling latest changes:"
echo "   sudo ${SCRIPT_DIR}/install_deploy_wrapper.sh"

