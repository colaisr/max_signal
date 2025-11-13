#!/bin/bash
# Production verification script - Run this on the production server
# Usage: ./scripts/verify_production.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Production Verification${NC}"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Not in project root directory${NC}"
    echo "   Please run: cd /srv/max-signal"
    exit 1
fi

# Check git status
echo -e "${BLUE}📥 Checking Git Status...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
LATEST_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/${CURRENT_BRANCH} 2>/dev/null || echo "unknown")
echo "   Current branch: ${CURRENT_BRANCH}"
echo "   Local commit: ${LATEST_COMMIT:0:8}"
if [ "$REMOTE_COMMIT" != "unknown" ]; then
    echo "   Remote commit: ${REMOTE_COMMIT:0:8}"
    if [ "$LATEST_COMMIT" != "$REMOTE_COMMIT" ]; then
        echo -e "${YELLOW}⚠️  Local and remote commits differ${NC}"
        echo "   Run: git pull origin ${CURRENT_BRANCH}"
    else
        echo -e "${GREEN}✅ Repository is up to date${NC}"
    fi
fi
echo ""

# Check backend service
echo -e "${BLUE}📦 Checking Backend Service...${NC}"
if systemctl is-active --quiet max-signal-backend; then
    echo -e "${GREEN}✅ Backend service is running${NC}"
    BACKEND_STATUS=$(systemctl is-active max-signal-backend)
    echo "   Status: ${BACKEND_STATUS}"
else
    echo -e "${RED}❌ Backend service is not running${NC}"
fi
echo ""

# Check frontend service
echo -e "${BLUE}🎨 Checking Frontend Service...${NC}"
if systemctl is-active --quiet max-signal-frontend; then
    echo -e "${GREEN}✅ Frontend service is running${NC}"
    FRONTEND_STATUS=$(systemctl is-active max-signal-frontend)
    echo "   Status: ${FRONTEND_STATUS}"
else
    echo -e "${RED}❌ Frontend service is not running${NC}"
fi
echo ""

# Check frontend build
echo -e "${BLUE}🏗️  Checking Frontend Build...${NC}"
if [ -d "frontend/.next" ]; then
    BUILD_TIME=$(stat -c %y frontend/.next 2>/dev/null || stat -f %Sm frontend/.next 2>/dev/null || echo "unknown")
    echo "   Build directory exists"
    echo "   Last modified: ${BUILD_TIME}"
    
    # Check if build is recent (within last 24 hours)
    if [ "$BUILD_TIME" != "unknown" ]; then
        echo -e "${GREEN}✅ Frontend build exists${NC}"
    fi
else
    echo -e "${RED}❌ Frontend build directory (.next) not found${NC}"
    echo "   Run: cd frontend && npm run build"
fi
echo ""

# Check backend virtual environment
echo -e "${BLUE}🐍 Checking Backend Environment...${NC}"
if [ -d "backend/.venv" ]; then
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
    if [ -f "backend/.venv/bin/uvicorn" ]; then
        echo "   Uvicorn found"
    else
        echo -e "${YELLOW}⚠️  Uvicorn not found in venv${NC}"
    fi
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
fi
echo ""

# Check recent logs for errors
echo -e "${BLUE}📋 Checking Recent Logs...${NC}"
echo "   Backend errors (last 10 lines):"
BACKEND_ERRORS=$(sudo journalctl -u max-signal-backend -n 10 --no-pager 2>/dev/null | grep -i error || echo "   No errors found")
echo "$BACKEND_ERRORS" | head -5
echo ""
echo "   Frontend errors (last 10 lines):"
FRONTEND_ERRORS=$(sudo journalctl -u max-signal-frontend -n 10 --no-pager 2>/dev/null | grep -i error || echo "   No errors found")
echo "$FRONTEND_ERRORS" | head -5
echo ""

# Health check endpoints
echo -e "${BLUE}🏥 Checking Health Endpoints...${NC}"
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
if echo "$BACKEND_HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is responding (HTTP ${FRONTEND_RESPONSE})${NC}"
else
    echo -e "${RED}❌ Frontend is not responding (HTTP ${FRONTEND_RESPONSE})${NC}"
fi
echo ""

# Summary and recommendations
echo -e "${BLUE}📋 Summary & Recommendations${NC}"
echo "=============================="
echo ""
echo "If you see CSS/static asset errors:"
echo "  1. Run: ./scripts/deploy.sh"
echo "  2. Run: ./scripts/restart_frontend.sh"
echo ""
echo "If services are not running:"
echo "  1. Check logs: sudo journalctl -u max-signal-backend -n 50"
echo "  2. Check logs: sudo journalctl -u max-signal-frontend -n 50"
echo "  3. Restart: sudo systemctl restart max-signal-backend max-signal-frontend"
echo ""

