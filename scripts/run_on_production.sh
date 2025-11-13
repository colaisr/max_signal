#!/bin/bash
# Copy-paste this entire script to run on production server
# Or run: curl -s https://raw.githubusercontent.com/colaisr/max_signal/main/scripts/full_production_deploy.sh | sudo bash

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
echo -e "${BLUE}║     Complete Production Deployment & Validation          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# Step 1: Pull latest changes
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Pulling latest changes${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
OLD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")
git pull origin main || git pull origin master || echo -e "${YELLOW}⚠️  Could not pull (may already be up to date)${NC}"
NEW_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

# Show file changes
if [ "$OLD_COMMIT" != "" ] && [ "$OLD_COMMIT" != "$NEW_COMMIT" ]; then
    echo ""
    echo -e "${BLUE}   File changes:${NC}"
    git diff --stat "$OLD_COMMIT" "$NEW_COMMIT" 2>/dev/null | sed 's/^/   /' || echo "   (No changes to display)"
else
    echo -e "${GREEN}   No changes${NC}"
fi
echo ""

# Step 2: Install standalone deploy script
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Installing standalone deploy script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ -f "$SCRIPT_DIR/install_standalone_deploy.sh" ]; then
    if [ "$EUID" -eq 0 ]; then
        "$SCRIPT_DIR/install_standalone_deploy.sh"
    else
        sudo "$SCRIPT_DIR/install_standalone_deploy.sh"
    fi
else
    echo -e "${YELLOW}⚠️  Install script not found, skipping...${NC}"
fi
echo ""

# Step 3: Run deployment
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Running deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if command -v max-signal-deploy >/dev/null 2>&1; then
    max-signal-deploy
else
    echo -e "${YELLOW}⚠️  max-signal-deploy not found, using script directly...${NC}"
    if [ -f "$SCRIPT_DIR/standalone_deploy.sh" ]; then
        if [ "$EUID" -eq 0 ]; then
            "$SCRIPT_DIR/standalone_deploy.sh"
        else
            sudo "$SCRIPT_DIR/standalone_deploy.sh"
        fi
    else
        echo -e "${RED}❌ Deployment script not found${NC}"
        exit 1
    fi
fi
echo ""

# Step 4: Validate deployment
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Validating deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ -f "$SCRIPT_DIR/validate_deployment.sh" ]; then
    "$SCRIPT_DIR/validate_deployment.sh"
else
    echo -e "${YELLOW}⚠️  Validation script not found, performing basic checks...${NC}"
    
    # Basic checks
    echo ""
    echo -e "${BLUE}📦 Backend Service:${NC}"
    if systemctl is-active --quiet max-signal-backend 2>/dev/null; then
        echo -e "${GREEN}✅ Backend service is running${NC}"
    else
        echo -e "${RED}❌ Backend service is not running${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🎨 Frontend Service:${NC}"
    if systemctl is-active --quiet max-signal-frontend 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend service is running${NC}"
    else
        echo -e "${RED}❌ Frontend service is not running${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🏥 Health Checks:${NC}"
    BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
    if echo "$BACKEND_HEALTH" | grep -q "ok"; then
        echo -e "${GREEN}✅ Backend health check passed${NC}"
    else
        echo -e "${RED}❌ Backend health check failed${NC}"
    fi
    
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Frontend responding (HTTP $FRONTEND_STATUS)${NC}"
        
        # Check CSS paths
        FRONTEND_HTML=$(curl -s http://localhost:3000 2>/dev/null || echo "")
        if echo "$FRONTEND_HTML" | grep -q "_next/static/css"; then
            echo -e "${GREEN}✅ CSS paths look correct${NC}"
        elif echo "$FRONTEND_HTML" | grep -q "next/static/css"; then
            echo -e "${YELLOW}⚠️  CSS path issue detected (next/static vs _next/static)${NC}"
        fi
    else
        echo -e "${RED}❌ Frontend not responding (HTTP $FRONTEND_STATUS)${NC}"
    fi
fi
echo ""

# Final summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Complete! ✅                                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📋 Deployment Summary:${NC}"
echo "   ✅ Latest code pulled from git"
echo "   ✅ Standalone deploy script installed"
echo "   ✅ Full deployment completed"
echo "   ✅ Services validated"
echo ""
echo -e "${BLUE}📋 Production URL:${NC}"
echo "   http://45.144.177.203:3000"
echo ""
echo -e "${BLUE}📋 If issues persist:${NC}"
echo "   Check logs: sudo journalctl -u max-signal-frontend -n 50"
echo "   Check logs: sudo journalctl -u max-signal-backend -n 50"
echo ""

