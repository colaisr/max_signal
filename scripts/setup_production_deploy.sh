#!/bin/bash
# Generate production deployment setup commands
# This script outputs the exact commands you need to run on your production server

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║     Production Deployment Setup - Copy & Paste Commands       ║
╚═══════════════════════════════════════════════════════════════╝

Run these commands on your production server:

# Step 1: Pull latest changes
cd /srv/max-signal
git pull origin main

# Step 2: Install standalone deploy script
sudo ./scripts/install_standalone_deploy.sh

# Step 3: Test the deployment (optional - does everything!)
max-signal-deploy

═══════════════════════════════════════════════════════════════

That's it! After installation, you can run 'max-signal-deploy' 
from anywhere to deploy everything automatically.

EOF

