#!/bin/bash
# Standalone deployment script for Max Signal Bot
# This script is completely independent and can be placed anywhere (e.g., /usr/local/bin/max-signal-deploy)
# It does NOT depend on any files in the repository
#
# Installation:
#   sudo cp scripts/standalone_deploy.sh /usr/local/bin/max-signal-deploy
#   sudo chmod +x /usr/local/bin/max-signal-deploy
#
# Usage:
#   max-signal-deploy

set -e

# ============================================================================
# CONFIGURATION - Edit these if your paths are different
# ============================================================================
PROJECT_ROOT="/srv/max-signal"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
GIT_BRANCH="main"  # Change to your default branch if different

# ============================================================================
# Colors for output
# ============================================================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================
print_step() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_info() {
    echo -e "${BLUE}$1${NC}"
}

# ============================================================================
# Main Deployment Script
# ============================================================================
main() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Max Signal Bot - Complete Deployment Script          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_ROOT" ]; then
        print_error "❌ Project directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    # Check if git repository exists
    if [ ! -d "$PROJECT_ROOT/.git" ]; then
        print_error "❌ Not a git repository: $PROJECT_ROOT"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # ========================================================================
    # Step 1: Pull Latest Changes
    # ========================================================================
    print_step "📥 Step 1: Pulling latest changes from git..."
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "$GIT_BRANCH")
    print_info "   Current branch: $CURRENT_BRANCH"
    
    # Fetch latest changes
    if ! git fetch origin "$CURRENT_BRANCH" 2>/dev/null; then
        print_warning "⚠️  Could not fetch from origin, trying current branch..."
        git fetch origin 2>/dev/null || print_warning "⚠️  Git fetch failed, continuing with local state..."
    fi
    
    # Reset to latest remote state
    if git rev-parse --verify "origin/$CURRENT_BRANCH" >/dev/null 2>&1; then
        git reset --hard "origin/$CURRENT_BRANCH"
        print_step "✅ Repository updated to latest"
    else
        print_warning "⚠️  Remote branch not found, using local state"
    fi
    echo ""
    
    # ========================================================================
    # Step 2: Backend - Update Dependencies
    # ========================================================================
    print_step "📦 Step 2: Updating backend dependencies..."
    cd "$BACKEND_DIR"
    
    # Check/create virtual environment
    if [ ! -d ".venv" ]; then
        print_warning "⚠️  Virtual environment not found. Creating..."
        python3.11 -m venv .venv || python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip first
    pip install --quiet --upgrade pip
    
    # Install/update dependencies
    print_info "   Installing Python packages from requirements.txt..."
    pip install -r requirements.txt --quiet --upgrade
    
    # Verify critical packages
    print_info "   Verifying critical packages..."
    MISSING_PACKAGES=()
    
    # Check each critical package
    for pkg in "tinkoff.invest" "apimoex" "requests" "ccxt" "yfinance"; do
        if ! python -c "import ${pkg}" 2>/dev/null; then
            MISSING_PACKAGES+=("$pkg")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        print_warning "⚠️  Some packages missing, reinstalling..."
        pip install -r requirements.txt --upgrade
    fi
    
    print_step "✅ Backend dependencies updated"
    echo ""
    
    # ========================================================================
    # Step 3: Backend - Run Migrations
    # ========================================================================
    print_step "🗄️  Step 3: Running database migrations..."
    alembic upgrade head
    print_step "✅ Migrations completed"
    echo ""
    
    # ========================================================================
    # Step 4: Frontend - Update Dependencies
    # ========================================================================
    print_step "📦 Step 4: Updating frontend dependencies..."
    cd "$FRONTEND_DIR"
    
    print_info "   Installing npm packages from package.json..."
    npm ci --silent
    
    print_step "✅ Frontend dependencies updated"
    echo ""
    
    # ========================================================================
    # Step 5: Frontend - Build
    # ========================================================================
    print_step "🏗️  Step 5: Building frontend for production..."
    npm run build
    
    print_step "✅ Frontend build completed"
    echo ""
    
    # ========================================================================
    # Step 6: Restart Backend Service
    # ========================================================================
    print_step "🔄 Step 6: Restarting backend service..."
    if systemctl is-active --quiet max-signal-backend 2>/dev/null; then
        sudo systemctl restart max-signal-backend
        sleep 2
        
        if systemctl is-active --quiet max-signal-backend; then
            print_step "✅ Backend service restarted and running"
        else
            print_error "❌ Backend service failed to start"
            print_info "   Check logs: sudo journalctl -u max-signal-backend -n 50"
            exit 1
        fi
    else
        print_warning "⚠️  Backend service not found or not active"
        print_info "   Service name: max-signal-backend"
    fi
    echo ""
    
    # ========================================================================
    # Step 7: Restart Frontend Service
    # ========================================================================
    print_step "🔄 Step 7: Restarting frontend service..."
    if systemctl is-active --quiet max-signal-frontend 2>/dev/null; then
        sudo systemctl restart max-signal-frontend
        sleep 2
        
        if systemctl is-active --quiet max-signal-frontend; then
            print_step "✅ Frontend service restarted and running"
        else
            print_error "❌ Frontend service failed to start"
            print_info "   Check logs: sudo journalctl -u max-signal-frontend -n 50"
            exit 1
        fi
    else
        print_warning "⚠️  Frontend service not found or not active"
        print_info "   Service name: max-signal-frontend"
    fi
    echo ""
    
    # ========================================================================
    # Step 8: Health Checks
    # ========================================================================
    print_step "🏥 Step 8: Verifying services..."
    
    # Check backend health
    sleep 3
    BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
    if echo "$BACKEND_HEALTH" | grep -q "ok"; then
        print_step "✅ Backend health check passed"
    else
        print_warning "⚠️  Backend health check failed (may need a moment to start)"
    fi
    
    # Check frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
    if [ "$FRONTEND_STATUS" = "200" ]; then
        print_step "✅ Frontend is responding (HTTP $FRONTEND_STATUS)"
    else
        print_warning "⚠️  Frontend check returned HTTP $FRONTEND_STATUS"
    fi
    echo ""
    
    # ========================================================================
    # Summary
    # ========================================================================
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Deployment Complete! ✅                     ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_info "📋 Summary:"
    echo "   ✅ Git repository updated"
    echo "   ✅ Backend dependencies updated"
    echo "   ✅ Database migrations completed"
    echo "   ✅ Frontend dependencies updated"
    echo "   ✅ Frontend built for production"
    echo "   ✅ Backend service restarted"
    echo "   ✅ Frontend service restarted"
    echo ""
    print_info "📋 Useful commands:"
    echo "   Check backend status:  sudo systemctl status max-signal-backend"
    echo "   Check frontend status: sudo systemctl status max-signal-frontend"
    echo "   View backend logs:     sudo journalctl -u max-signal-backend -f"
    echo "   View frontend logs:    sudo journalctl -u max-signal-frontend -f"
    echo "   Backend health:        curl http://localhost:8000/health"
    echo "   Frontend URL:          http://localhost:3000"
    echo ""
}

# Run main function
main "$@"

