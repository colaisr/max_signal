#!/bin/bash
# Validate deployment after running max-signal-deploy
# Usage: ./scripts/validate_deployment.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Deployment Validation${NC}"
echo "=========================="
echo ""

# Check backend service
echo -e "${BLUE}📦 Backend Service:${NC}"
if systemctl is-active --quiet max-signal-backend 2>/dev/null; then
    echo -e "${GREEN}✅ Service is running${NC}"
    BACKEND_STATUS=$(systemctl is-active max-signal-backend)
    echo "   Status: $BACKEND_STATUS"
else
    echo -e "${RED}❌ Service is not running${NC}"
fi

# Check frontend service
echo ""
echo -e "${BLUE}🎨 Frontend Service:${NC}"
if systemctl is-active --quiet max-signal-frontend 2>/dev/null; then
    echo -e "${GREEN}✅ Service is running${NC}"
    FRONTEND_STATUS=$(systemctl is-active max-signal-frontend)
    echo "   Status: $FRONTEND_STATUS"
else
    echo -e "${RED}❌ Service is not running${NC}"
fi

# Health checks
echo ""
echo -e "${BLUE}🏥 Health Checks:${NC}"

# Backend health
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
if echo "$BACKEND_HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

# Frontend response
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend responding (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}❌ Frontend not responding (HTTP $FRONTEND_STATUS)${NC}"
fi

# Check for CSS issues
echo ""
echo -e "${BLUE}🎨 Frontend Static Assets:${NC}"
FRONTEND_HTML=$(curl -s http://localhost:3000 2>/dev/null || echo "")
if echo "$FRONTEND_HTML" | grep -q "next/static/css"; then
    echo -e "${YELLOW}⚠️  Potential CSS path issue detected${NC}"
    echo "   (next/static vs _next/static)"
elif echo "$FRONTEND_HTML" | grep -q "_next/static/css"; then
    echo -e "${GREEN}✅ CSS paths look correct${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify CSS paths${NC}"
fi

echo ""
echo -e "${BLUE}📋 Summary${NC}"
echo "=========================="
if systemctl is-active --quiet max-signal-backend && systemctl is-active --quiet max-signal-frontend && [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Deployment appears successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Some issues detected. Check logs:${NC}"
    echo "   sudo journalctl -u max-signal-backend -n 50"
    echo "   sudo journalctl -u max-signal-frontend -n 50"
fi
echo ""

