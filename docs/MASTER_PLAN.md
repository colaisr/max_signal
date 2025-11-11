## Max Signal Bot — MVP Master Plan

### 1) Purpose and Scope

- **Goal**: Build an MVP system that analyzes markets from multiple sources and produces actionable trading posts in Telegram style, with intrastep transparency for prompt control and tuning. Later add backtesting to replay the same analysis on historical data.
- **Early usage**: Few users; focus on logic quality, prompt control, and result observability.
- **Triggering**: Manual at first; scheduled (daily; later hourly/1m/5m) after.
- **Outputs**: 
  - UI to trigger and view runs with all intrastep data.
  - Telegram channel post with the final merged analysis.
- **AI approach**: Heavy usage of LLM agents/tools; LLM provider switchable via OpenAI-compatible API using OpenRouter for simplicity and cost/uptime benefits (`https://openrouter.ai/`).

Constraints and preferences:
- Separate backend and frontend repositories (work in parallel and commit separately).
- Configuration values live in code with a local, non-committed file for secrets (avoid .env in VCS).
- Single VM deployment without Docker; simple “pull → install deps → restart” flow.


### 2) Tech Stack

- Backend
  - Python 3.11+, FastAPI (async-first), Uvicorn
  - MySQL via SQLAlchemy (or SQLModel) + Alembic migrations (baseline from day one)
  - APScheduler for schedules
  - HTTP client: httpx (async)
  - OpenAI-compatible client pointed at OpenRouter base URL (for easy model switching)
  - Telegram: aiogram (async) or python-telegram-bot (sync)
  - Logging: structlog
  - Data adapters: CCXT (crypto), yfinance (equities)
  - Config module: `app/config_local.py` (gitignored) holding keys for OpenRouter and Telegram

- Frontend
  - Next.js (React) + TailwindCSS + shadcn/ui
  - Data fetching: React Query (TanStack Query) or SWR
  - Pages: Dashboard (trigger run), Run detail (intrasteps), Settings

- Deployment (single VM, no Docker)
  - Two repos checked out to `/srv/max-signal/backend` and `/srv/max-signal/frontend`
  - Backend: Python venv, Uvicorn via systemd; connects to local or external MySQL
  - Frontend: Next.js production build, `npm run start` via systemd
  - Scripts: `deploy_backend.sh` and `deploy_frontend.sh`
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
  - Data Providers: CCXT, yfinance (others later)

- Data model (MySQL)
  - `instruments`: id, symbol, type, exchange
  - `analysis_runs`: id, trigger_type (manual/scheduled), instrument_id, timeframe, status (queued/running/succeeded/failed), created_at, finished_at, cost_est_total
  - `analysis_steps`: id, run_id, step_name (wyckoff/smc/vsa/delta/ict/merge), input_blob, output_blob, llm_model, tokens, cost_est, created_at
  - `telegram_posts`: id, run_id, message_text, status (pending/sent/failed), message_id, sent_at
  - `data_cache`: id, key, payload, fetched_at, ttl_seconds

- Core services
  - Data adapters: normalized OHLCV fetch; light feature extraction (structure hints, volume stats if available)
  - Agent orchestrator: runs intrasteps (Wyckoff, SMC, VSA, Delta, ICT) using stable prompts and tool schemas; then merges into final Telegram post
  - Telegram publisher: split message ≤4096 chars; retry/send; record `message_id`
  - Scheduler: APScheduler triggers daystart (daily), extend to intervals later

- API (FastAPI)
  - `POST /runs` → manual trigger (instrument, timeframe, options) → `run_id`
  - `GET /runs/{id}` → run status + intrastep outputs
  - `POST /runs/{id}/publish` → send to Telegram
  - `GET /instruments` → list available instruments
  - `GET /health` → health probe

- Frontend (Next.js)
  - Dashboard: form to trigger Daystart; shows latest runs table
  - Run detail: timeline of steps with prompts/outputs; final post preview; “Publish to Telegram”
  - Settings: model choice, Telegram channel id, schedule time (saved to backend config endpoint or stored locally on server)

### 3a) UX Specification

- Information architecture
  - Dashboard: quick Daystart trigger, recent runs, system status; watchlist of instruments/timeframes.
  - Run history: filterable table (instrument, timeframe, status, model, date), bulk actions.
  - Run detail: step timeline (Wyckoff, SMC, VSA, Delta, ICT, Merge) with expandable prompts/outputs, model, tokens/cost; final Telegram preview; publish/copy.
  - Research Lab: prompt playground with model switching; save experiments as templates.
  - Signals: feed of generated signals with direction/entry/stop/targets; filters; future subscriptions.
  - Backtesting: scenario builder (date range, instruments), results table (win rate, RR), chart overlays.
  - Settings: models/routing, data sources/instruments, Telegram config, scheduler.

- Patterns
  - Left sidebar nav; topbar status chips; dark-first theme.
  - Timeline + accordions for steps; stream outputs when available.
  - Prompt versioning with inline diff; instrument picker and timeframe chips; transparency cues (data source/time, model, tokens/cost).
  - Keyboard shortcuts: N (new run), R (retry), P (publish).

- MVP pages
  - Dashboard, Run history, Run detail, Settings (core), minimal Research Lab (single step).


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
- `data_cache` table for short-lived cache to reduce repeated fetches


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
  - `/srv/max-signal/backend` (git repo, Python venv at `.venv/`)
  - `/srv/max-signal/frontend` (git repo)
  - `/srv/max-signal/deploy_backend.sh`, `/srv/max-signal/deploy_frontend.sh`

- Systemd units
  - `max-signal-backend.service`: runs Uvicorn with 2 workers, working dir `/srv/max-signal/backend`
  - `max-signal-frontend.service`: runs `npm run start -- --port 3000` in `/srv/max-signal/frontend`

- Deploy scripts (manual run after push)
  - Backend: pull/reset to `origin/main`, create venv, `pip install -r requirements.txt`, run Alembic migrations, `systemctl restart max-signal-backend`
  - Frontend: pull/reset to `origin/main`, `npm ci`, `npm run build`, `systemctl restart max-signal-frontend`

- Environment
  - Backend binds to `0.0.0.0:8000`
  - Frontend binds to `0.0.0.0:3000`, `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
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

### 10) Security and Observability

- Secrets only on server in `config_local.py` (never committed)
- Log aggregation: journald via `journalctl -u ...`
- Basic request/step logging with structlog; redact secrets
- Health endpoint for uptime checks


### 11) Milestones with Acceptance Criteria

1) Foundation (1–2 days)
   - Backend skeleton (FastAPI app with `/health`)
   - MySQL wiring (SQLAlchemy models) and Alembic initialized with baseline migration
   - Frontend skeleton (Next.js app + Tailwind + simple page)
   - Local config examples prepared
   - Acceptance:
     - `GET /health` returns 200.
     - Alembic baseline applies successfully to local MySQL.
     - Frontend renders and fetches `/health`.

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
  - [ ] Backend health passes
  - [ ] MySQL reachable; Alembic baseline applied
  - [ ] Frontend renders and calls backend

- Data adapters
  - [ ] Crypto OHLCV fetched
  - [ ] Equity OHLCV fetched
  - [ ] Normalization verified

- Authentication
  - [ ] Login/logout works with session cookie
  - [ ] Admin-only pages and actions enforced

- Daystart pipeline
  - [ ] All 5 method steps produce outputs
  - [ ] Merge step produces Telegram-ready post
  - [ ] Costs/tokens recorded

- UI for runs
  - [ ] Manual trigger from UI works
  - [ ] Run details show prompts/outputs
  - [ ] Final preview matches style template

- Telegram
  - [ ] Channel posting works
  - [ ] Long messages split correctly

- Scheduling
  - [ ] Daily job fired on schedule
  - [ ] Run completes without manual action

- Deployment
  - [ ] deploy scripts idempotent
  - [ ] systemd services restart and stay active

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

- [ ] Foundation
- [ ] Data adapters
- [ ] Daystart pipeline
- [ ] UI for runs
- [ ] Telegram integration
- [ ] Scheduling
- [ ] Deployment (single VM)
- [ ] Backtesting (Phase 2)


### 15) Next Actions

1) Confirm initial instruments (e.g., BTC/USDT and AAPL) and timeframes (M15/H1).
2) Scaffold backend and frontend repos and wire `/health` and a minimal Dashboard.
3) Implement Daystart intrasteps and Merge, with OpenRouter default model and token/cost logging.
4) Add Telegram publisher and daily schedule.


---

Notes:
- OpenRouter provides a unified OpenAI-compatible interface to many models which simplifies switching and increases availability: `https://openrouter.ai/`.
- This document is the living source of truth; update checkboxes and milestone notes as we progress.


