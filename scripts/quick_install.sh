#!/bin/bash
# Quick installation script - Run this on production server
# This script does everything automatically

set -e

PROJECT_ROOT="/srv/max-signal"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Quick Production Deployment Setup                      ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root for installation
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Not running as root. Some steps may require sudo.${NC}"
    echo ""
fi

# Step 1: Navigate to project
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_ROOT${NC}"
    echo "   Please ensure the project is cloned to $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"
echo -e "${GREEN}✅ Found project at: $PROJECT_ROOT${NC}"
echo ""

# Step 2: Pull latest changes
echo -e "${BLUE}📥 Pulling latest changes from git...${NC}"
if git pull origin main 2>/dev/null || git pull origin master 2>/dev/null; then
    echo -e "${GREEN}✅ Repository updated${NC}"
else
    echo -e "${YELLOW}⚠️  Could not pull (may already be up to date)${NC}"
fi
echo ""

# Step 3: Check if install script exists
if [ ! -f "$SCRIPT_DIR/install_standalone_deploy.sh" ]; then
    echo -e "${RED}❌ Installation script not found: $SCRIPT_DIR/install_standalone_deploy.sh${NC}"
    echo "   Please ensure you've pulled the latest changes"
    exit 1
fi

# Step 4: Install standalone deploy script
echo -e "${BLUE}📦 Installing standalone deploy script...${NC}"
if [ "$EUID" -eq 0 ]; then
    "$SCRIPT_DIR/install_standalone_deploy.sh"
else
    sudo "$SCRIPT_DIR/install_standalone_deploy.sh"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete! ✅                            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "   Run deployment:"
echo "   $ max-signal-deploy"
echo ""
echo "   This will automatically:"
echo "   ✅ Pull latest git changes"
echo "   ✅ Update backend dependencies"
echo "   ✅ Run database migrations"
echo "   ✅ Update frontend dependencies"
echo "   ✅ Build frontend for production"
echo "   ✅ Restart backend service"
echo "   ✅ Restart frontend service"
echo "   ✅ Verify services are running"
echo ""

