# Forward Plan - Max Signal Bot MVP

## ✅ Completed Milestones

1. **Foundation** - Backend/Frontend skeletons, MySQL setup, Alembic migrations
2. **Data Adapters + Minimal UI** - CCXT/yfinance adapters, caching, dashboard
3. **Daystart Pipeline + UI Integration** - All 6 analysis steps, OpenRouter integration
4. **Polish UI** - Enhanced step display, Telegram preview, expandable timeline

## 🎯 Remaining MVP Milestones

### **Option A: Core MVP Completion (Recommended First)**

**4. Authentication** (0.5-1 day)
- Backend: Session-based auth endpoints (`POST /api/auth/login`, `POST /api/auth/logout`)
- Frontend: Login page, protect admin routes
- User model: Email/password, roles (`admin`, `trader`)
- Session cookies with `SESSION_SECRET`
- **Why now:** Needed before Telegram integration (admin-only publishing)

**5. Telegram Integration** (0.5-1 day)
- Backend: `POST /api/runs/{id}/publish` endpoint
- Use `python-telegram-bot` or `aiogram` library
- Message splitting (Telegram 4096 char limit)
- Add "Publish to Telegram" button in UI
- **Why now:** Core feature - users need to publish results

**6. Scheduling** (0.5-1 day)
- APScheduler daily job at configured time (`DAYSTART_SCHEDULE`)
- Create runs automatically
- Optional: UI to view/manage scheduled jobs
- **Why now:** Automation - core MVP feature

**7. Deployment** (1-2 days)
- Single VM setup (Ubuntu/Debian)
- Systemd service files for backend/frontend
- `deploy.sh` script (git pull, install deps, restart)
- Domain/SSL configuration (optional)
- **Why now:** Need production environment

**Total: ~4-6 days to complete MVP**

---

### **Option B: Quick Wins First**

**4. Telegram Integration** (0.5-1 day) - Skip auth for now, add later
**5. Scheduling** (0.5-1 day)
**6. Deployment** (1-2 days)
**7. Authentication** (0.5-1 day) - Add before going public

**Total: ~3-5 days to MVP (without auth initially)**

---

## 📋 Detailed Breakdown

### **4. Authentication** (if chosen first)

**Backend:**
- Create `User` model (email, password_hash, role)
- Alembic migration
- `POST /api/auth/login` - validate credentials, set session cookie
- `POST /api/auth/logout` - clear session
- `GET /api/auth/me` - get current user
- Middleware to protect routes (check session)

**Frontend:**
- `/login` page with email/password form
- Redirect to login if not authenticated
- Show user info in header/navbar
- Protect admin routes (only `admin` role can publish)

**Dependencies:**
- `bcrypt` for password hashing (already in requirements)
- Session management (FastAPI sessions)

---

### **5. Telegram Integration**

**Backend:**
- Install `python-telegram-bot` or `aiogram`
- `POST /api/runs/{id}/publish` endpoint
- Get merge step output (final Telegram post)
- Split message if > 4096 chars (preserve formatting)
- Send to configured channel (`TELEGRAM_CHANNEL_ID`)
- Store publish status/timestamp in DB (optional)

**Frontend:**
- Add "Publish to Telegram" button in run detail page
- Show success/error feedback
- Disable button if already published

**Configuration:**
- `TELEGRAM_BOT_TOKEN` in `config_local.py`
- `TELEGRAM_CHANNEL_ID` in `config_local.py`

---

### **6. Scheduling**

**Backend:**
- APScheduler setup in `main.py`
- Daily job at `DAYSTART_SCHEDULE` (e.g., "08:00")
- Job creates run with default instrument/timeframe
- Optional: Multiple schedules (different instruments/timeframes)
- Optional: UI to view scheduled jobs

**Configuration:**
- `DAYSTART_SCHEDULE` in `config_local.py` (already exists)

**Optional Enhancements:**
- Pause/resume scheduling
- View scheduled runs history
- Manual trigger from UI

---

### **7. Deployment**

**Server Setup:**
- Ubuntu/Debian VM
- MySQL server
- Python 3.11+ and Node.js 18+
- Git repository clone

**Backend Service:**
- Systemd service file: `max-signal-backend.service`
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Auto-restart on failure
- Logs to `/var/log/max-signal/backend.log`

**Frontend Service:**
- Systemd service file: `max-signal-frontend.service`
- Runs `npm run build` then `npm start` (production mode)
- Or use PM2/nginx reverse proxy
- Auto-restart on failure

**Deploy Script:**
- `scripts/deploy.sh`:
  1. `git pull origin main`
  2. `cd backend && source .venv/bin/activate && pip install -r requirements.txt`
  3. `cd frontend && npm install && npm run build`
  4. `alembic upgrade head` (if migrations)
  5. `systemctl restart max-signal-backend max-signal-frontend`

**Optional:**
- Nginx reverse proxy (port 80/443 → backend:8000, frontend:3000)
- SSL certificate (Let's Encrypt)
- Domain configuration

---

## 🤔 Discussion Points

### **1. Authentication Priority**
- **Option A:** Add auth first (more secure, proper user management)
- **Option B:** Skip for now, add later (faster MVP, less secure)
- **Recommendation:** Option A if multiple users, Option B if single user initially

### **2. Telegram Integration**
- Do you have Telegram bot token and channel ID ready?
- Should publishing be manual only, or auto-publish on completion?
- Need message formatting adjustments?

### **3. Scheduling**
- Default instrument/timeframe for daily runs?
- Multiple schedules (different instruments)?
- Timezone handling (server time vs UTC)?

### **4. Deployment**
- Do you have a VM ready?
- Preferred hosting provider?
- Domain name available?
- SSL certificate needed?

### **5. MVP Scope**
- Is backtesting needed for MVP, or Phase 2?
- Any other features critical for MVP?

---

## 📊 Current Status

**Working Features:**
- ✅ Market data fetching (crypto + equities)
- ✅ Data caching (5min TTL)
- ✅ Full analysis pipeline (6 steps)
- ✅ Cost tracking
- ✅ UI with step visualization
- ✅ Telegram post generation

**Missing for MVP:**
- ⏳ User authentication
- ⏳ Telegram publishing
- ⏳ Scheduled runs
- ⏳ Production deployment

---

## 🚀 Recommended Next Steps

1. **Decide on authentication priority** (now vs later)
2. **Get Telegram credentials** (bot token + channel ID)
3. **Choose deployment approach** (VM ready? hosting provider?)
4. **Start with Telegram Integration** (most visible value)
5. **Then Scheduling** (automation)
6. **Finally Deployment** (production)

**What would you like to tackle first?**

