#!/bin/bash
# Install standalone deploy script to /usr/local/bin
# This script installs a completely independent deployment script
# Usage: sudo ./scripts/install_standalone_deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STANDALONE_SCRIPT="${SCRIPT_DIR}/standalone_deploy.sh"
TARGET="/usr/local/bin/max-signal-deploy"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 Installing Standalone Deploy Script${NC}"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Check if standalone script exists
if [ ! -f "$STANDALONE_SCRIPT" ]; then
    echo -e "${RED}❌ Standalone script not found: $STANDALONE_SCRIPT${NC}"
    exit 1
fi

# Backup old script if it exists
if [ -f "$TARGET" ]; then
    echo -e "${YELLOW}⚠️  Found existing script at $TARGET${NC}"
    BACKUP="${TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "   Backing up to: $BACKUP"
    cp "$TARGET" "$BACKUP"
fi

# Install standalone script
echo "📋 Installing standalone deploy script to $TARGET..."
cp "$STANDALONE_SCRIPT" "$TARGET"
chmod +x "$TARGET"

echo ""
echo -e "${GREEN}✅ Standalone deploy script installed successfully!${NC}"
echo ""
echo "📋 Usage:"
echo "   max-signal-deploy"
echo ""
echo "📋 What it does:"
echo "   ✅ Pulls latest changes from git"
echo "   ✅ Updates backend dependencies"
echo "   ✅ Runs database migrations"
echo "   ✅ Updates frontend dependencies"
echo "   ✅ Builds frontend for production"
echo "   ✅ Restarts backend service"
echo "   ✅ Restarts frontend service"
echo "   ✅ Verifies services are running"
echo ""
echo "📋 Configuration:"
echo "   Edit $TARGET to change:"
echo "   - PROJECT_ROOT (default: /srv/max-signal)"
echo "   - GIT_BRANCH (default: main)"
echo ""
echo -e "${GREEN}✅ Ready to use!${NC}"
echo ""

