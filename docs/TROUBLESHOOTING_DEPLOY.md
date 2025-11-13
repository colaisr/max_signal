# Deployment Troubleshooting Guide

## Issue: `max-signal-deploy` Script Not Working Properly

### Problem

If you have a standalone copy of `max-signal-deploy` at `/usr/local/bin/max-signal-deploy`, it may:
- Be outdated (doesn't update when you pull git changes)
- Have incorrect path resolution
- Fail to find the project directory
- Not include latest features or fixes

### Solution: Install Standalone Deploy Script (Recommended)

The standalone deploy script is completely independent and does everything automatically:

```bash
cd /srv/max-signal
sudo ./scripts/install_standalone_deploy.sh
```

This installs a complete, self-contained deployment script that:
- ✅ Never gets overwritten by git pulls
- ✅ Is completely independent (doesn't depend on repo files)
- ✅ Does everything automatically (pull, update, migrate, build, restart)
- ✅ Can be customized without affecting git repo

**Usage:**
```bash
max-signal-deploy  # Run from anywhere!
```

**Alternative Options:**

**Option 1: Use Script Directly from Repo**
```bash
cd /srv/max-signal
./scripts/deploy.sh
./scripts/restart_backend.sh
./scripts/restart_frontend.sh
```

**Option 2: Create Symlink**
```bash
sudo rm /usr/local/bin/max-signal-deploy  # Remove old copy
sudo ln -s /srv/max-signal/scripts/deploy.sh /usr/local/bin/max-signal-deploy
```

### Verification

After installing the wrapper, test it:

```bash
# Should show the latest deploy script output
max-signal-deploy

# Or verify it points to the right location
which max-signal-deploy
cat /usr/local/bin/max-signal-deploy
```

### Common Issues

**Issue: "Not a git repository" error**
- **Cause:** Script can't find project root
- **Fix:** Ensure you're running from `/srv/max-signal` or install the wrapper

**Issue: "Permission denied"**
- **Cause:** Script not executable
- **Fix:** `chmod +x /usr/local/bin/max-signal-deploy` or reinstall wrapper

**Issue: Script runs but doesn't update frontend**
- **Cause:** Old script version missing frontend build step
- **Fix:** Install wrapper or use script directly from repo

**Issue: CSS/static asset errors after deployment**
- **Cause:** Frontend build is outdated or corrupted
- **Fix:** 
  ```bash
  cd /srv/max-signal
  ./scripts/deploy.sh  # Rebuilds frontend
  ./scripts/restart_frontend.sh
  ```

### Best Practices

1. **Always use scripts from git repo** - They're automatically updated when you pull
2. **Use wrapper script** - If you need a global command, use the wrapper
3. **Check script version** - Compare `/usr/local/bin/max-signal-deploy` with `/srv/max-signal/scripts/deploy.sh`
4. **Run from project directory** - When possible, use `./scripts/deploy.sh` directly

### Quick Fix for Current Issue

If `max-signal-deploy` is not working:

```bash
# 1. SSH into production server
ssh user@your-server

# 2. Install wrapper (recommended)
cd /srv/max-signal
sudo ./scripts/install_deploy_wrapper.sh

# 3. Or use script directly
cd /srv/max-signal
./scripts/deploy.sh

# 4. Restart services
./scripts/restart_backend.sh
./scripts/restart_frontend.sh
```

