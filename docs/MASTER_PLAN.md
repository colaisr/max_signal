## Max Signal Bot — MVP Master Plan

### 1) Purpose and Scope

- **Goal**: Build an MVP system that analyzes markets from multiple sources and produces actionable trading posts in Telegram style, with intrastep transparency for prompt control and tuning. Later add backtesting to replay the same analysis on historical data.
- **Early usage**: Few users; focus on logic quality, prompt control, and result observability.
- **Triggering**: Manual at first; scheduled (daily; later hourly/1m/5m) after.
- **Outputs**: 
  - UI to trigger and view runs with all intrastep data.
  - Telegram direct messages to all users who started the bot with the final merged analysis.
- **AI approach**: Heavy usage of LLM agents/tools; LLM provider switchable via OpenAI-compatible API using OpenRouter for simplicity and cost/uptime benefits (`https://openrouter.ai/`).

Constraints and preferences:
- Monorepo structure (backend and frontend in same repository).
- Configuration values live in code with a local, non-committed file for secrets (avoid .env in VCS).
- Single VM deployment without Docker; simple "pull → install deps → restart" flow.


### 2) Tech Stack

- Backend
  - Python 3.11+, FastAPI (async-first), Uvicorn
  - MySQL via SQLAlchemy (or SQLModel) + Alembic migrations (baseline from day one)
  - APScheduler for schedules
  - HTTP client: httpx (async)
  - OpenAI-compatible client pointed at OpenRouter base URL (for easy model switching)
  - Telegram: aiogram (async) or python-telegram-bot (sync)
  - Logging: structlog
  - Data adapters: CCXT (crypto), yfinance (equities), Tinkoff Invest API (MOEX - Russian stocks/bonds/ETFs)
  - Config module: `app/config_local.py` (gitignored) holding keys for OpenRouter and Telegram

- Frontend
  - Next.js (React) + TailwindCSS + shadcn/ui
  - Data fetching: React Query (TanStack Query) or SWR
  - Pages: Dashboard (trigger run), Run detail (intrasteps), Settings

- Deployment (single VM, no Docker)
  - Monorepo checked out to `/srv/max-signal/` (contains `backend/` and `frontend/` subdirectories)
  - Backend: Python venv, Uvicorn via systemd; connects to local or external MySQL
  - Frontend: Next.js production build, `npm run start` via systemd
  - Scripts: `deploy.sh` (pulls repo), `restart_backend.sh`, `restart_frontend.sh`
  - Local MySQL defaults (dev): host `localhost`, port `3306`, db `max_signal_dev`, user `max_signal_user`
    - SQLAlchemy DSN: `mysql+pymysql://max_signal_user:YOUR_PASSWORD@localhost:3306/max_signal_dev?charset=utf8mb4`
    - Use script: `/Users/colakamornik/Desktop/max_signal_bot/scripts/mysql_local_setup.sql` (edit password, then apply with a privileged MySQL user)
    - Note: This creates a NEW database on the same MySQL server (separate from infrazen_dev, which belongs to another project and should not be touched)

- References
  - OpenRouter: `https://openrouter.ai/`


### 3) High-Level Architecture

- Components
  - Backend service: APIs, agent orchestration, data adapters, scheduling, persistence
  - Frontend app: trigger runs, view details, publish to Telegram
  - Telegram Bot Publisher: posts final message to the channel, handles message splitting and retries
  - Data Providers: CCXT (crypto), yfinance (equities), Tinkoff Invest API (MOEX)

- Data model (MySQL)
  - `instruments`: id, symbol, type, exchange, figi (Tinkoff FIGI for MOEX instruments), is_enabled (admin toggle for dropdown visibility)
  - `analysis_runs`: id, trigger_type (manual/scheduled), instrument_id, timeframe, status (queued/running/succeeded/failed), created_at, finished_at, cost_est_total
  - `analysis_steps`: id, run_id, step_name (wyckoff/smc/vsa/delta/ict/merge), input_blob, output_blob, llm_model, tokens, cost_est, created_at
- `telegram_posts`: id, run_id, message_text, status (pending/sent/failed), message_id, sent_at
- `telegram_users`: id, chat_id, username, first_name, last_name, is_active, started_at, last_message_at, created_at, updated_at
- `data_cache`: id, key, payload, fetched_at, ttl_seconds

- Core services
  - Data adapters: normalized OHLCV fetch; light feature extraction (structure hints, volume stats if available)
  - Agent orchestrator: runs intrasteps (Wyckoff, SMC, VSA, Delta, ICT) using stable prompts and tool schemas; then merges into final Telegram post
  - Telegram publisher: split message ≤4096 chars; send to all active users who started the bot; record `message_id`; handle partial failures gracefully
- Telegram bot handler: process `/start`, `/help`, `/status` commands; automatically register users when they start the bot
  - Scheduler: APScheduler triggers daystart (daily), extend to intervals later

- API (FastAPI)
  - `POST /runs` → manual trigger (instrument, timeframe, options) → `run_id`
  - `GET /runs/{id}` → run status + intrastep outputs
  - `POST /runs/{id}/publish` → send to Telegram
  - `GET /instruments` → list available instruments
  - `GET /health` → health probe

- Frontend (Next.js)
  - Dashboard: form to trigger Daystart; shows latest runs table
  - Run detail: timeline of steps with prompts/outputs; final post preview; "Publish to Telegram"
  - Settings: model choice, Telegram bot token, active users count, schedule time (saved to backend config endpoint or stored locally on server)

### 3a) UX Specification & Product Architecture

**Navigation Structure:**
- **Home (`/`)**: Landing page with product overview, quick stats, recent activity, quick actions
- **Analyses (`/analyses`)**: Browse and configure analysis types/pipelines
  - List view: Cards showing all available analysis types
  - Detail view: Complete pipeline visualization with step configuration
- **Runs (`/runs`)**: View all analysis runs (history, status, results)
- **Schedules (`/schedules`)**: Manage scheduled analysis jobs
- **Settings (`/settings`)**: Configuration management (models, data sources, Telegram, preferences)
- **Backtesting (`/backtesting`)**: Phase 2 feature

**Key UX Principles:**
- **Pipeline Transparency**: Users can see complete pipeline configuration before running:
  - Step sequence visualization
  - LLM model per step (with ability to change)
  - System and user prompts (viewable/editable for admin)
  - Data sources/tools used
  - Estimated cost and duration
- **Extensibility**: Architecture supports multiple analysis types (Daystart, Intraday SMC, Weekly Overview, Custom)
- **User Roles**: Currently admin-only; future: Admin (full access) and Trader (view + run, no config changes)

**Analyses Page (`/analyses`):**
- **List View**: Card grid showing:
  - Analysis name and description
  - Number of steps
  - Estimated cost range
  - Last run timestamp
  - Actions: "Configure", "Run", "View History"
  
- **Detail View (`/analyses/{id}`)**: 
  - Analysis overview (name, description, use case, defaults)
  - **Pipeline Visualization**: Shows all steps with:
    - Step name and order
    - LLM model (dropdown to change)
    - System prompt (view/edit)
    - User prompt template (with variables: `{instrument}`, `{timeframe}`, `{market_data}`)
    - Data source/tools used
    - Temperature, max tokens
  - Actions: "Run Analysis" (with instrument/timeframe selector), "Save Configuration"

**Runs Page (`/runs`):**
- Dashboard view with filters (analysis type, status, instrument, date range)
- Runs table with columns: ID, Analysis Type, Instrument, Timeframe, Status, Steps Completed, Cost, Created/Finished
- Detail view: Timeline with expandable steps, final Telegram post preview, publish button

**Settings Page (`/settings`):**
- Tabbed interface:
  - **LLM Models**: Available models with advanced filtering and syncing capabilities
    - **Model Syncing**: "Sync from OpenRouter" button fetches latest available models from OpenRouter API
    - **Search & Filters**: 
      - Search by model name, provider, or description
      - Filter by provider (dropdown)
      - "Enabled only" toggle to show only enabled models
      - "Free to use models" toggle to filter free models (models with "free" in name)
    - **Scrollable List**: Models displayed in scrollable container (max height 500px) for easy browsing
    - Enable/disable toggles for each model
    - Models show: display name, provider, model ID, description, max tokens, cost per 1K tokens
    - New models from sync are disabled by default (admin can enable manually)
  - **Data Sources**: CCXT exchanges, yfinance markets, cache settings
  - **Telegram**: Bot token, channel ID, publishing settings, active users count
  - **OpenRouter Configuration**: API key for OpenRouter (required for LLM calls and model syncing)
  - **Tinkoff Invest API**: API token for MOEX instruments (required for Russian stocks/bonds/ETFs)
  - **Available Instruments**: Searchable list of all instruments (crypto, equities, MOEX) with enable/disable toggles
    - Enabled instruments appear in dropdown selectors
    - Instruments fetched dynamically from APIs (MOEX ISS API for Russian market)
    - Supports search and scrollable view (shows 10 items at a time)
  - **User Preferences**: Profile, theme, timezone, notifications
  - **System** (admin): Feature flags, cost limits

**Design Patterns:**
- Left sidebar navigation (or top nav bar for MVP)
- Dark-first theme
- Timeline + accordions for steps
- Status badges with colors (green=succeeded, blue=running, red=failed, yellow=queued)
- Expandable sections for prompts/outputs
- Copy-to-clipboard functionality
- Real-time updates while pipeline runs (polling every 2s)


### 4) Daystart Analysis Pipeline (MVP Feature)

- Inputs
  - `instrument` (e.g., `BTC/USDT`, `AAPL`), `timeframe` (e.g., M15/H1), `session_day`
  - OHLCV lookback window (configurable)

- Intrasteps (each step persists `input_blob` and `output_blob`)
  1) Wyckoff — phase (Accumulation/Distribution/Markup/Markdown), context, likely scenario
  2) SMC — structure (BOS/CHoCH/OB/FVG/Liquidity), key levels, liquidity events
  3) VSA — activity of large participants, signals (no demand/supply, stopping volume, climactic action), effort vs result
  4) Delta — dominance, anomalous delta, absorption, divergence
  5) ICT — liquidity manipulation, PD arrays, FVG/OB return zones, optimal entries
  6) Merge — unify into a Telegram-ready post following the exact style below

- Telegram style and template (final merge step must honor):

```
💬 ПРОМТ ДЛЯ АНАЛИЗА РЫНКА (в формате поста для TELEGRAM)

Сделай анализ рынка в форме готового сообщения для Телеграм-канала —
структурно, списками, без таблиц и без воды.
Текст должен быть как полноценный пост с логикой профессионального разбора и планом действий.

⸻

🔹 Требования к оформлению:
 • Обязательно должен быть заголовок, отражающий суть анализа.
 • Далее — блоки с анализом по каждому методу.
 • Всё в едином стиле телеграм-поста: коротко, точно, информативно.
 • В конце — внутридневной торговый план и таймфрейм для закрепления входа.

⸻

🔹 Проанализируй рынок по 5 подходам:
 • Wyckoff
 • Smart Money Concepts (SMC)
 • ICT
 • VSA
 • Delta-анализ

⸻

🔹 Пошагово:
1️⃣ Wyckoff — фаза рынка, контекст, вероятный сценарий.
2️⃣ SMC — BOS, CHoCH, OB, FVG, Liquidity Pools, ключевые уровни/возвраты.
3️⃣ VSA — активность крупных участников; no demand/supply; stopping volume; climactic action; effort vs result.
4️⃣ Delta — доминация, аномалии, абсорбция, дивергенции, удержание.
5️⃣ ICT — манипуляции ликвидностью, зоны возврата (FVG, PD Arrays), точки входа.

⸻

🔹 Объединение:
 • Wyckoff — контекст цикла.
 • SMC — структура и зоны ликвидности.
 • VSA+Delta — подтверждение силы/слабости.
 • ICT — точка входа после манипуляции и возврата в дисбаланс.

Логика: Контекст → Структура → Подтверждение силы → Манипуляция → Вход → Удержание.

⸻

🔹 Манипуляционный план (Smart Money / ICT):
 • Где вероятен сбор ликвидности (над хаями/под лоями).
 • Где ложный пробой и возврат в диапазон.
 • Какая зона возврата (FVG/OB) — ключ для входа.
 • Где цели и стопы маркетмейкера.
 • Что подтвердит сценарий (BOS или реакция по дельте).

⸻

🔹 Внутридневной торговый план («если-то»):
 • Если закрепление выше ключевой зоны → приоритет лонг; вход после теста + подтверждения по дельте.
 • Если ниже зоны ликвидности → приоритет шорт; вход после возврата в дисбаланс.
 • Если консолидация без силы → ожидание; работа от границ диапазона.

📍 Укажи: приоритет направления, зону входа, зону стопа, ближайшие цели, таймфрейм закрепления (M15/H1).

⸻

🔹 Итог: три сценария
 • 🟢 Бычий — при закреплении выше ключевой зоны.
 • 🔴 Медвежий — при закреплении ниже.
 • ⚪ Нейтральный — при консолидации.
```

- LLM usage
  - System prompt defines role, output rules, style.
  - Each step uses structured prompt with any computed context (e.g., candidate levels).
  - Record model used, token counts, and estimated cost.
  - Default model is configurable; routed through OpenRouter for easy switching.


### 5) APIs (initial)

- `POST /runs`
  - Body: `{ instrument, timeframe, options }`
  - Result: `{ run_id }`
- `GET /runs/{id}`
  - Result: `{ status, steps: [{name, input, output, model, tokens}], final_post }`
- `POST /runs/{id}/publish`
  - Sends final post to configured Telegram channel; returns `{ status, message_id }`
- `GET /instruments`
  - Returns supported instruments and exchanges
- `GET /health`


### 6) Data Adapters

- CCXT (crypto): normalized OHLCV, adjustable timeframe, exchange-specific symbol mapping
- yfinance (equities): OHLCV daily/intraday; handle API limits and caching
- Tinkoff Invest API (MOEX): Russian stocks, bonds, ETFs from Moscow Exchange
  - Uses FIGI (Financial Instrument Global Identifier) for instrument identification
  - FIGI mapping cached in `instruments` table (`figi` column)
  - Automatic FIGI lookup via Tinkoff API when instrument is first used
  - Requires Tinkoff API token configured in Settings
  - Supports timeframes: M1, M5, M15, H1, D1
- `data_cache` table for short-lived cache to reduce repeated fetches
- Instrument routing: `DataService` automatically selects adapter based on `exchange` field in `instruments` table


### 7) Scheduling

- APScheduler in backend
  - Daily job (“daystart”) at configured time(s)
  - Future: additional interval jobs (hourly/1m/5m) per instrument
  - Jobs enqueue internal “run” creation the same way as manual triggers


### 8) Telegram Integration

- Bot token and channel id stored in `config_local.py` on server
- Split messages into ≤4096 characters
- Retry policy: exponential backoff on rate limits (429) and transient errors


### 9) Deployment (Single VM, no Docker)

- Directory layout
  - `/srv/max-signal/` (monorepo git repo)
    - `backend/` (Python venv at `backend/.venv/`)
    - `frontend/`
    - `scripts/` (deployment scripts)
  - `/srv/max-signal/scripts/deploy.sh` (pulls entire repo)
  - `/srv/max-signal/scripts/restart_backend.sh` (updates backend deps, migrations, restarts)
  - `/srv/max-signal/scripts/restart_frontend.sh` (updates frontend deps, builds, restarts)

- Systemd units
  - `max-signal-backend.service`: runs Uvicorn with 2 workers, working dir `/srv/max-signal/backend`
  - `max-signal-frontend.service`: runs `npm run start -- --port 3000` in `/srv/max-signal/frontend`

- Deploy scripts (manual run after push)
  - Step 1: `./scripts/deploy.sh` - Complete deployment preparation:
    - Pulls latest changes from `origin/main` (or current branch)
    - Updates backend dependencies (`requirements.txt`)
    - Runs database migrations (`alembic upgrade head`)
    - Updates frontend dependencies (`package.json`)
    - Builds frontend for production (`npm run build`)
  - Step 2: `./scripts/restart_backend.sh` - Restarts backend service (syncs deps/migrations if needed)
  - Step 3: `./scripts/restart_frontend.sh` - Restarts frontend service (rebuilds if needed)

- Environment
  - Backend binds to `0.0.0.0:8000`
  - Frontend binds to `0.0.0.0:3000`; API base URL is centralized in `frontend/lib/config.ts` and automatically matches the current hostname (e.g., `http://localhost:8000` when visiting `http://localhost:3000`). For local scripts (`start_all.sh`), prefer `http://localhost:3000` consistently.
  - Reverse proxy optional for MVP; can add Nginx/Caddy later for TLS/domains
  - MySQL connection configured in `app/config_local.py` (local dev DB and prod DB endpoints)

### 10a) Authentication and User Accounts

- Requirements
  - Email/password login; roles: `admin`, `trader` (viewer).
  - Session cookie (HttpOnly, secure in prod), server-side validation; no tokens stored in frontend.
  - Endpoints: `/auth/login`, `/auth/logout`, `/auth/me` (profile), `/auth/register` (admin only).
  - Passwords hashed with bcrypt; rate limiting on login.
  - Protected routes: publish to Telegram, Settings, scheduler changes (admin only).
  - Tables: `users` (id, email, hashed_password, role, created_at, last_login_at), optional `user_sessions`.

- Frontend
  - Login page; guard protected pages; show current user and role.
  - Error states and lockouts; logout action.

#### 10b) Local Auth Flow Notes & Troubleshooting (Dev)

- Standard session auth
  - Backend sets `maxsignal_session` as an HttpOnly cookie with `SameSite=lax`, `Path=/` (set `secure=True` in production over HTTPS).
  - Frontend checks auth via `GET /api/auth/me` only on protected routes; public routes (`/`, `/login`) do not trigger the check.
- Single source of API base URL
  - `frontend/lib/config.ts` exports `API_BASE_URL` which derives from `window.location.hostname` when env is not set. This keeps cookies same‑site in dev (avoids `localhost` vs `127.0.0.1` mismatches).
  - Actionable rule: when using `scripts/start_all.sh`, open the app at `http://localhost:3000` (backend runs at `http://localhost:8000`). Avoid mixing with `127.0.0.1`.
- Navigation behavior
  - `Navigation` skips `useAuth()` on `/` and `/login` to avoid unnecessary requests on public pages.
- When configs change
  - Restart the frontend dev server to pick up changes to `API_BASE_URL` or auth hooks.
- Quick troubleshooting
  - If reload logs you out: ensure FE page host equals BE request host; verify `/api/auth/login` response includes `Set-Cookie`; confirm cookie appears under the matching host in DevTools; clear cookies for the other host and stick to one (`localhost` recommended with `start_all.sh`); restart the FE dev server.

### 10) Security and Observability

- Secrets only on server in `config_local.py` (never committed)
- Log aggregation: journald via `journalctl -u ...`
- Basic request/step logging with structlog; redact secrets
- Health endpoint for uptime checks


### 11) Milestones with Acceptance Criteria

1) Foundation (1–2 days) ✅ **COMPLETED**
   - Backend skeleton (FastAPI app with `/health`)
   - MySQL wiring (SQLAlchemy models) and Alembic initialized with baseline migration
   - Frontend skeleton (Next.js app + Tailwind + simple page)
   - Local config examples prepared
   - Local MySQL database created (`max_signal_dev`)
   - Alembic migrations applied (all tables created)
   - Start/stop automation scripts (`start_all.sh`, `stop_all.sh`)
   - Acceptance:
     - `GET /health` returns 200. ✅
     - Alembic baseline applies successfully to local MySQL. ✅
     - Frontend renders and fetches `/health`. ✅
     - Both servers start/stop via scripts. ✅

2) Data adapters (1–2 days)
   - CCXT and yfinance adapters returning normalized OHLCV for given instrument/timeframe
   - Basic feature builder (structure hints, volume stats)
   - Acceptance:
     - Manual run logs show fetched candles for at least 1 crypto and 1 equity symbol.

2a) Authentication (0.5–1 day)
   - Backend auth endpoints with session cookie; bcrypt password hashing
   - User table migration; seed first admin user (manual or script)
   - Frontend login page; protect Settings/Publish
   - Acceptance:
     - Can login/logout; `/auth/me` returns current user.
     - Admin-only Settings and publish routes enforced.

3) Daystart pipeline (3–5 days)
   - Implement steps: Wyckoff, SMC, VSA, Delta, ICT, Merge
   - Persist prompt inputs/outputs per step, model, tokens, cost
   - Acceptance:
     - `POST /runs` creates a run and completes with stored intrasteps.
     - `GET /runs/{id}` shows all intrastep outputs and final Telegram-ready post.

4) UI for runs (1–2 days)
   - Dashboard: trigger Daystart, view latest runs
   - Run detail page: intrasteps, final post preview, publish button
   - Acceptance:
     - Triggering from UI creates a run; page polls status until complete.

5) Telegram integration (0.5–1 day)
   - Publish final message to channel with splitting and retries
   - Acceptance:
     - Clicking “Publish to Telegram” sends the post; message_id stored.

6) Scheduling (0.5–1 day)
   - APScheduler daily job; toggle via config
   - Acceptance:
     - At scheduled time, run is created and completed automatically.

7) Deployment to single VM (0.5–1 day)
   - Systemd units and deploy scripts created and tested
   - Acceptance:
     - `deploy_backend.sh` and `deploy_frontend.sh` run end-to-end and services restart cleanly.

8) Backtesting (Phase 2, 2–4 days)
   - Historical data fetch and batch runs through the same pipeline
   - UI to inspect backtest outputs and compare with live
   - Acceptance:
     - Backtest job runs N historical sessions and stores outputs like live runs.


### 12) Validation Checklist (per milestone)

- Foundation
  - [x] Backend health passes
  - [x] MySQL reachable; Alembic baseline applied
  - [x] Frontend renders and calls backend

- Data adapters
  - [x] Crypto OHLCV fetched ✅
  - [x] Equity OHLCV fetched ✅
  - [x] MOEX OHLCV fetched via Tinkoff API ✅
  - [x] FIGI mapping and caching implemented ✅
  - [x] Instrument routing based on exchange field ✅
  - [x] Normalization verified ✅
  - [x] Caching implemented ✅
  - [x] Minimal UI working ✅
  - [x] Instrument management UI (enable/disable, search) ✅

- Authentication
  - [ ] Login/logout works with session cookie
  - [ ] Admin-only pages and actions enforced

- Daystart pipeline
  - [x] All 6 method steps produce outputs ✅
  - [x] Merge step produces Telegram-ready post ✅
  - [x] Costs/tokens recorded ✅
  - [x] Pipeline orchestrator working ✅
  - [x] Steps visible in UI ✅

- UI for runs
  - [ ] Manual trigger from UI works
  - [ ] Run details show prompts/outputs
  - [ ] Final preview matches style template

- Telegram
  - [x] Direct messaging to users works ✅
  - [x] Long messages split correctly ✅
  - [x] Bot handler for /start command ✅
  - [x] Automatic user registration ✅
  - [x] Error handling for partial failures ✅

- Scheduling
  - [ ] Daily job fired on schedule
  - [ ] Run completes without manual action

- Deployment
  - [x] deploy scripts created ✅
  - [x] systemd service files created ✅
  - [x] deployment documentation written ✅
  - [ ] deploy scripts tested in production
  - [ ] systemd services tested and verified

- Backtesting (Phase 2)
  - [ ] Historical batch runs complete
  - [ ] Outputs stored and viewable


### 13) Risk Log and Mitigations

- Model variance / provider outages
  - Route via OpenRouter to switch models/providers quickly; keep step prompts deterministic.
- Cost control
  - Record tokens; add caps/alerts; prefer concise prompts; cache data.
- Data quality/latency
  - Cache OHLCV briefly; retry on provider errors; support switching providers.
- Telegram limits
  - Implement message splitting and backoff.
- Single-VM limits
  - Keep concurrency modest; consider moving to a process manager pool if needed.


### 14) Progress Tracker (MVP)

- [x] Foundation ✅ (Completed: Backend/Frontend skeletons, MySQL models, Alembic setup, health endpoints)
- [x] Data Adapters + Minimal UI ✅ (Completed: CCXT/yfinance adapters, normalized data, caching, dashboard, run detail page)
- [x] Daystart Pipeline + UI Integration ✅ (Completed: All 6 analysis steps, OpenRouter integration, pipeline orchestrator, step display)
- [x] Polish UI ✅ (Completed: Enhanced step display, Telegram preview, expandable timeline, copy functionality)
- [x] Navigation & Layout ✅ (Completed: Navigation bar, shared layout, all pages updated)
- [x] Analyses Page & Pipeline Configuration ✅ (Completed: List page, detail page with pipeline visualization, runs filtering, live updates)
- [x] Authentication ✅ (Completed: Session-based auth, login/logout, route protection, admin user creation)
- [x] Analysis Configuration Editing ✅ (Completed: Editable models, prompts, data sources before running)
- [x] Telegram Integration ✅ (Completed: Backend publish endpoint, message splitting, Settings page, credentials from AppSettings, TelegramUser model, bot handler for /start/help/status commands, automatic user registration, direct messaging to users, error handling for partial failures)
- [x] Settings Page Enhancements ✅ (Completed: Model syncing from OpenRouter API, search and filter functionality for models, scrollable model list, enabled/free filters, provider filter dropdown)
- [ ] Refactor pipeline to use analysis_type configuration (accepts custom_config, needs full implementation)
- [ ] Scheduling
- [x] Deployment (single VM) ✅ (Scripts and documentation ready - see `docs/PRODUCTION_DEPLOYMENT.md`)
- [ ] Backtesting (Phase 2)


### 15) Next Actions

**✅ Completed:**
- Foundation milestone (skeletons, MySQL setup, migrations, automation scripts)

**🎯 Recommended Development Strategy:**

**Hybrid Approach: Build Minimal UI Early for Testing**

Since we need to test and observe the analysis pipeline, we should build a **minimal UI** early rather than testing only via API endpoints. This gives us:
- Visual feedback during development
- Ability to see intrastep outputs in real-time
- Faster debugging and validation
- Early UX validation

**Revised Milestone Order:**

**1. Data Adapters + Minimal UI Foundation** ✅ **COMPLETED** (1–2 days)
- Implement CCXT/yfinance adapters ✅
- Create normalized OHLCV data structure ✅
- **Build minimal UI:** Basic dashboard with instrument selector and "Run Analysis" button ✅
- **Build minimal run detail page:** Show run status and basic outputs ✅
- **Testing:** Can trigger a data fetch and see results in UI ✅
- Fixed: Database migration for MEDIUMTEXT payload column ✅

**2. Daystart Pipeline + UI Integration** ✅ **COMPLETED** (3–5 days)
- Implement analysis steps (Wyckoff, SMC, VSA, Delta, ICT, Merge) ✅
- OpenRouter integration for LLM calls ✅
- **Enhance UI:** Show intrastep timeline with expandable steps ✅ (Basic implementation)
- **Testing:** Full pipeline visible in UI, can see each step's prompt/output ✅
- Verified: All 6 steps execute successfully, costs tracked, Telegram post generated ✅

**3. Polish UI** ✅ **COMPLETED** (1 day)
- Improve run detail page with better formatting ✅
- Add Telegram post preview section with copy functionality ✅
- Add expandable accordion-style step timeline ✅
- Enhanced visual hierarchy and UX ✅
- **Testing:** Complete user flow works end-to-end ✅

**4. Polish UI** ✅ **COMPLETED** (1 day)
- Improve run detail page with better formatting ✅
- Add Telegram post preview section with copy functionality ✅
- Add expandable accordion-style step timeline ✅
- Enhanced visual hierarchy and UX ✅
- **Testing:** Complete user flow works end-to-end ✅

**5. Analyses Page & Pipeline Configuration** ✅ **COMPLETED** (2-3 days)
- Create `/analyses` list page (show all analysis types) ✅
- Create `/analyses/{id}` detail page with pipeline visualization ✅
- Add `analysis_types` table to store analysis configurations ✅
- Show step configuration (models, prompts, data sources) before running ✅
- Create `/runs` page with filtering by analysis type ✅
- Fix live updates for run steps (polling every 2s) ✅
- **Testing:** Can view pipeline config, run analysis, see live updates ✅

**6. Navigation & Layout** ✅ **COMPLETED** (1 day)
- Add top navigation bar (Home, Analyses, Runs, Schedules, Settings) ✅
- Create layout component with navigation ✅
- Update all pages to use shared layout ✅
- **Testing:** Navigation works across all pages ✅

**7. Authentication** (0.5-1 day)
- Backend auth endpoints (login/logout)
- Frontend login page
- Session management
- **Note:** Admin-only for MVP, no trader role yet

**8. Telegram Integration** (0.5-1 day)
- Publish endpoint
- Message splitting
- Add "Publish to Telegram" button in run detail

**7. Authentication** ✅ **COMPLETED** (0.5-1 day)
- Backend auth endpoints (login/logout) ✅
- Frontend login page ✅
- Session management ✅
- Route protection ✅
- Admin user creation script ✅
- **Testing:** Can login, logout, protected routes work ✅

**8. Analysis Configuration Editing** ✅ **COMPLETED** (1 day)
- Editable configuration UI in analysis detail page ✅
- Edit models, prompts, temperature, max_tokens, data sources ✅
- Reset to defaults functionality ✅
- Custom config passed to backend ✅
- **Testing:** Can edit config before running analysis ✅

**9. Telegram Integration** ✅ **COMPLETED** (0.5-1 day)
- Backend publish endpoint ✅
- Message splitting ✅
- Frontend publish button ✅
- Settings page for Telegram bot token ✅
- Telegram publisher reads credentials from Settings (AppSettings table) ✅
- **Telegram User Management:**
  - Created `TelegramUser` model to store users who started the bot ✅
  - Bot handler for `/start`, `/help`, `/status` commands ✅
  - Automatic user registration when users send `/start` ✅
  - Messages sent to all active users (not channel) ✅
  - Settings page shows active users count ✅
- **Error Handling:**
  - Detailed error reporting for partial failures ✅
  - Frontend shows warnings when some users fail to receive messages ✅
  - Backend logs detailed error information for debugging ✅
- **Testing:** Can publish to Telegram, users automatically registered via /start command ✅

**10. Settings Page Enhancements** ✅ **COMPLETED** (1 day)
- **Model Management:**
  - Added "Sync from OpenRouter" button to fetch latest models from OpenRouter API ✅
  - Backend endpoint `/api/settings/models/sync` fetches models via OpenRouter API ✅
  - New models added to database (disabled by default) ✅
  - Existing models preserved (not overwritten) ✅
- **Advanced Filtering:**
  - Search by model name, provider, or description ✅
  - Provider filter dropdown (dynamically populated) ✅
  - "Enabled only" toggle to filter enabled models ✅
  - "Free to use models" toggle to filter free models ✅
- **UI Improvements:**
  - Scrollable model list container (max height 500px) ✅
  - Model count display ("X models found") ✅
  - Empty state message when no models match ✅
  - Hover effects and consistent styling ✅
  - Responsive layout with flex-wrap for smaller screens ✅
- **Testing:** Can sync models from API, filter by provider/enabled/free, search works correctly ✅

**Why This Approach:**
- ✅ Can test visually instead of just API calls
- ✅ See intrastep data immediately (critical for prompt tuning)
- ✅ Faster iteration on analysis logic
- ✅ Early validation of UX flow
- ✅ FastAPI `/docs` still available for API testing
- ✅ Minimal UI can be polished later without blocking backend work


---

Notes:
- OpenRouter provides a unified OpenAI-compatible interface to many models which simplifies switching and increases availability: `https://openrouter.ai/`.
- This document is the living source of truth; update checkboxes and milestone notes as we progress.


