# Monorepo Deployment Summary

## Changes Made

Updated all deployment documentation and scripts to reflect **monorepo structure** instead of separate repositories.

## New Deployment Flow

### 1. Complete Deployment Preparation
```bash
cd /srv/max-signal
./scripts/deploy.sh
```
This script:
- Pulls latest changes from monorepo (works with current branch)
- Updates backend dependencies (`requirements.txt`)
- Runs database migrations (`alembic upgrade head`)
- Updates frontend dependencies (`package.json`)
- Builds frontend for production (`npm run build`)

### 2. Restart Services (as needed)
```bash
# If backend changed
./scripts/restart_backend.sh

# If frontend changed
./scripts/restart_frontend.sh
```

## Scripts Created

- ✅ `scripts/deploy.sh` - Complete deployment preparation (pull, deps, migrations, build)
- ✅ `scripts/restart_backend.sh` - Restarts backend service (syncs deps/migrations if needed)
- ✅ `scripts/restart_frontend.sh` - Restarts frontend service (rebuilds if needed)

## Scripts Removed

- ❌ `scripts/deploy_backend.sh` - Replaced by `deploy.sh` + `restart_backend.sh`
- ❌ `scripts/deploy_frontend.sh` - Replaced by `deploy.sh` + `restart_frontend.sh`

## Updated Documentation

- ✅ `docs/MASTER_PLAN.md` - Updated to reflect monorepo structure
- ✅ `docs/PRODUCTION_DEPLOYMENT.md` - Updated deployment steps
- ✅ `docs/DEPLOYMENT_DISCUSSION.md` - Updated deployment flow
- ✅ `docs/DEPLOYMENT_QUICK_REFERENCE.md` - Updated commands
- ✅ `README.md` - Updated repository description

## Key Changes

1. **Single Repository**: Both backend and frontend are in the same git repository
2. **Single Pull**: One `deploy.sh` script pulls the entire repo
3. **Separate Restarts**: Individual restart scripts for backend/frontend
4. **Directory Structure**: `/srv/max-signal/` contains `backend/`, `frontend/`, and `scripts/`

## Production Setup

```bash
# Clone monorepo
cd /srv/max-signal
git clone <repo-url> .

# Setup backend
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp app/config_local.example.py app/config_local.py
# Edit config_local.py
alembic upgrade head

# Setup frontend
cd ../frontend
npm ci
npm run build

# Install systemd services
cd ..
./scripts/install_systemd_services.sh
sudo systemctl enable max-signal-backend max-signal-frontend
sudo systemctl start max-signal-backend max-signal-frontend
```

## Regular Deployments

```bash
cd /srv/max-signal
# Step 1: Pull, update dependencies, run migrations, build
./scripts/deploy.sh

# Step 2: Restart services (as needed)
./scripts/restart_backend.sh   # if backend changed
./scripts/restart_frontend.sh  # if frontend changed
```

