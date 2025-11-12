# Production Deployment Discussion

## Current Status

✅ **Completed:**
- Application is fully functional locally
- All core features working (analysis pipeline, Telegram integration, authentication)
- API keys moved to database (`AppSettings` table) via Settings UI
- Telegram bot handler with automatic user registration
- Database migrations ready

📋 **Ready for Production:**
- Deployment scripts created (`deploy_backend.sh`, `deploy_frontend.sh`)
- Systemd service files created
- Production deployment guide written

## Key Decisions Needed

### 1. Server Infrastructure

**Questions:**
- Do you have a VM/server ready? (Ubuntu/Debian recommended)
- Is MySQL already set up, or do we need to install it?
- Will you use a reverse proxy (Nginx/Caddy) for SSL/domain, or direct access?

**Recommendations:**
- Use reverse proxy with SSL for production (security, professional appearance)
- Local MySQL is fine for MVP, but consider remote if you plan to scale
- Single VM is sufficient for MVP (as per MASTER_PLAN.md)

### 2. Configuration Management

**Current Architecture:**
- `config_local.py` → MySQL DSN, SESSION_SECRET (server-only, gitignored)
- `AppSettings` table → OpenRouter API key, Telegram bot token (set via UI)

**Decisions:**
- ✅ **DONE**: API keys moved to database (more secure, can be updated via UI)
- ⚠️ **TODO**: SESSION_SECRET still in `config_local.py` (acceptable for MVP)
- ⚠️ **TODO**: MySQL password in `config_local.py` (acceptable for MVP, consider secrets manager later)

### 3. Database Setup

**Options:**
- **Option A**: New production database on same MySQL server
- **Option B**: Separate MySQL server (better isolation)
- **Option C**: Managed MySQL service (AWS RDS, DigitalOcean, etc.)

**Recommendation for MVP:** Option A (simplest, sufficient for early usage)

**Action Items:**
- [ ] Create production database: `max_signal_prod`
- [ ] Create production MySQL user with strong password
- [ ] Run migrations: `alembic upgrade head`
- [ ] Create initial admin user

### 4. Deployment Process

**Created Scripts:**
- `scripts/deploy.sh` - Complete deployment preparation:
  - Pulls latest changes from monorepo
  - Updates backend dependencies (`requirements.txt`)
  - Runs database migrations
  - Updates frontend dependencies (`package.json`)
  - Builds frontend for production
- `scripts/restart_backend.sh` - Restarts backend service (syncs deps/migrations if needed)
- `scripts/restart_frontend.sh` - Restarts frontend service (rebuilds if needed)
- `scripts/install_systemd_services.sh` - Installs systemd service files

**Deployment Flow:**
1. Push code to `main` branch (monorepo)
2. SSH to server
3. Run `./scripts/deploy.sh` - This does everything: pull, update deps, migrations, build
4. Run `./scripts/restart_backend.sh` if backend changed
5. Run `./scripts/restart_frontend.sh` if frontend changed

**Questions:**
- Do you want automated deployments (GitHub Actions, webhooks)?
- Or manual deployments (current scripts) are fine?

**Recommendation:** Manual for MVP, automate later if needed

### 5. Environment Variables

**Backend:**
- `MYSQL_DSN` - In `config_local.py` (production database)
- `SESSION_SECRET` - In `config_local.py` (generate with `openssl rand -hex 32`)
- OpenRouter API key - Set via Settings UI (stored in `AppSettings` table)
- Telegram bot token - Set via Settings UI (stored in `AppSettings` table)

**Frontend:**
- `NEXT_PUBLIC_API_BASE_URL` - Set in `.env.production` or environment
  - Local: `http://localhost:8000`
  - With reverse proxy: `https://your-domain.com/api`

**Action Items:**
- [ ] Clone monorepo to `/srv/max-signal/`
- [ ] Create `backend/app/config_local.py` on production server
- [ ] Generate strong `SESSION_SECRET`
- [ ] Set `NEXT_PUBLIC_API_BASE_URL` for frontend (in `.env.production` or environment)

### 6. Security Considerations

**Current State:**
- ✅ Session-based authentication (secure cookies)
- ✅ Passwords hashed with bcrypt
- ✅ API keys in database (not in code)
- ✅ Secrets in gitignored `config_local.py`

**To Do:**
- [ ] Set proper file permissions: `chmod 600 app/config_local.py`
- [ ] Configure firewall (only allow necessary ports)
- [ ] Set up SSL/HTTPS (via reverse proxy)
- [ ] Regular database backups
- [ ] Monitor logs for errors

**Recommendations:**
- Use reverse proxy (Nginx/Caddy) for SSL termination
- Set up automated database backups (daily)
- Monitor service logs regularly

### 7. Monitoring & Maintenance

**Basic Monitoring:**
- Systemd service status: `systemctl status max-signal-backend`
- Logs: `journalctl -u max-signal-backend -f`
- Health endpoint: `curl http://localhost:8000/health`

**Future Enhancements:**
- Uptime monitoring (UptimeRobot, Pingdom)
- Error alerting (Sentry, etc.)
- Performance monitoring
- Cost tracking (OpenRouter API usage)

**Action Items:**
- [ ] Set up log rotation (systemd handles this)
- [ ] Create database backup script
- [ ] Document monitoring procedures

### 8. Telegram Bot Setup

**Current Implementation:**
- Bot token stored in database (via Settings UI)
- Bot handler processes `/start`, `/help`, `/status` commands
- Users automatically registered when they send `/start`
- Messages sent to all active registered users

**Production Considerations:**
- ✅ Bot token can be updated via Settings UI (no code changes needed)
- ✅ Users identified by `chat_id` (persistent, survives bot restarts)
- ⚠️ **Important**: Users need to send `/start` to bot after deployment
- ⚠️ **Important**: Bot must be running (handled by systemd service)

**Action Items:**
- [ ] Create Telegram bot via @BotFather (if not done)
- [ ] Get bot token
- [ ] Set bot token in Settings UI after deployment
- [ ] Test `/start` command
- [ ] Verify user registration works

### 9. Initial Setup Checklist

**Before First Deployment:**
- [ ] Server provisioned (Ubuntu/Debian)
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] MySQL installed and running
- [ ] Git installed
- [ ] SSH access configured
- [ ] Firewall configured

**During Deployment:**
- [ ] Clone monorepo to `/srv/max-signal/`
- [ ] Create `backend/app/config_local.py` with production MySQL DSN and SESSION_SECRET
- [ ] Run database migrations
- [ ] Create initial admin user
- [ ] Install systemd services
- [ ] Start services
- [ ] Configure API keys via Settings UI
- [ ] Test full flow

**After Deployment:**
- [ ] Verify health endpoints
- [ ] Test login
- [ ] Test analysis run
- [ ] Test Telegram publishing
- [ ] Set up database backups
- [ ] Configure monitoring (optional)

## Questions for Discussion

1. **Server Setup:**
   - Do you have a server ready, or do we need to provision one?
   - What's the server IP/domain?
   - Do you want to use a reverse proxy (Nginx/Caddy) for SSL?

2. **Database:**
   - Will you use local MySQL or remote?
   - Do you have MySQL credentials ready?
   - Should we create a separate production database?

3. **Deployment:**
   - Do you want to deploy now, or wait?
   - Manual deployments OK, or want automation?
   - Any specific deployment time/window?

4. **Configuration:**
   - Do you have OpenRouter API key ready?
   - Do you have Telegram bot token ready?
   - Any specific model preferences?

5. **Monitoring:**
   - Do you want to set up external monitoring (UptimeRobot, etc.)?
   - How do you want to receive alerts?

6. **Backups:**
   - How often should we backup the database?
   - Where should backups be stored?
   - Do you want automated backups?

## Next Steps

1. **Review this document** and answer the questions above
2. **Review `PRODUCTION_DEPLOYMENT.md`** for detailed steps
3. **Prepare server** (if not ready)
4. **Gather credentials** (MySQL, OpenRouter, Telegram)
5. **Schedule deployment** (when ready)
6. **Execute deployment** following the guide
7. **Verify everything works**
8. **Set up monitoring and backups**

## Files Created

- `docs/PRODUCTION_DEPLOYMENT.md` - Complete deployment guide
- `scripts/deploy.sh` - Pulls latest changes from monorepo
- `scripts/restart_backend.sh` - Backend restart script (deps, migrations, restart)
- `scripts/restart_frontend.sh` - Frontend restart script (deps, build, restart)
- `scripts/systemd/max-signal-backend.service` - Backend systemd service
- `scripts/systemd/max-signal-frontend.service` - Frontend systemd service
- `scripts/install_systemd_services.sh` - Service installation script

All scripts are executable and ready to use!

**Note:** This is a monorepo structure. Both backend and frontend are in the same repository.

