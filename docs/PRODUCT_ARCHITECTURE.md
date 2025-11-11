# Max Signal Bot - Product Architecture & UX Specification

## Product Vision

**Max Signal Bot** is an AI-powered market analysis platform that generates professional trading insights using multiple analytical methodologies (Wyckoff, SMC, VSA, Delta, ICT). The platform combines LLM agents with market data to produce actionable Telegram-ready posts, with full transparency into each analysis step for prompt tuning and quality control.

**Core Value Propositions:**
- **Transparency**: See every step of the analysis pipeline (prompts, models, outputs)
- **Flexibility**: Multiple analysis types, configurable pipelines, model switching
- **Automation**: Scheduled runs, automated publishing to Telegram
- **Extensibility**: Easy to add new analysis types, data sources, and LLM models

---

## Information Architecture

### Navigation Structure

```
┌─────────────────────────────────────────────────┐
│  Max Signal Bot                    [User Menu ▼] │
├─────────────────────────────────────────────────┤
│  [Home] [Analyses] [Runs] [Schedules] [Settings]│
└─────────────────────────────────────────────────┘
```

**Primary Navigation:**
1. **Home** (`/`) - Landing page with product overview, quick stats, recent activity
2. **Analyses** (`/analyses`) - Browse and configure analysis types/pipelines
3. **Runs** (`/runs`) - View all analysis runs (history, status, results)
4. **Schedules** (`/schedules`) - Manage scheduled analysis jobs
5. **Settings** (`/settings`) - User preferences, model config, data sources, Telegram

**Secondary Navigation (within sections):**
- **Runs**: Dashboard view, Detail view, Filters/Search
- **Analyses**: List view, Detail/Configuration view, Create new
- **Schedules**: List view, Create/Edit schedule, Job history

---

## Page Specifications

### 1. Home (`/`) - Landing Page

**Purpose:** Product introduction, quick access, system overview

**Content:**
- **Hero Section**
  - Product name and tagline
  - Brief description: "AI-powered market analysis with full transparency"
  - CTA: "Run Analysis" button (quick trigger)
  
- **Quick Stats Dashboard**
  - Total runs executed
  - Success rate
  - Average cost per run
  - Last run timestamp
  
- **Recent Activity Feed**
  - Last 5 runs with status badges
  - Quick links to run details
  
- **Quick Actions**
  - "Run Daystart Analysis" (pre-configured)
  - "View All Runs"
  - "Manage Schedules"
  
- **Product Capabilities** (collapsible)
  - Supported analysis methods
  - Available data sources
  - Supported instruments

**User Flow:**
- New users: Understand what the platform does
- Returning users: Quick access to common actions

---

### 2. Analyses (`/analyses`) - Analysis Types Management

**Purpose:** Browse, configure, and understand available analysis pipelines

**List View (`/analyses`):**
- **Card Grid Layout**
  - Each card represents one analysis type (e.g., "Daystart Analysis", "Intraday SMC", "Weekly Overview")
  - Card shows:
    - Analysis name and description
    - Number of steps
    - Estimated cost range
    - Last run timestamp
    - Status badge (active/inactive)
  - Actions: "Configure", "Run", "View History"

**Detail View (`/analyses/{id}`):**
- **Analysis Overview**
  - Name, description, use case
  - Default instrument/timeframe
  - Estimated duration and cost
  
- **Pipeline Visualization**
  ```
  ┌─────────────────────────────────────────────┐
  │  Pipeline Steps                             │
  ├─────────────────────────────────────────────┤
  │  1️⃣ Data Fetch                              │
  │     └─ Source: Binance (CCXT)               │
  │     └─ Instrument: BTC/USDT                 │
  │     └─ Timeframe: H1                        │
  │                                             │
  │  2️⃣ Wyckoff Analysis                        │
  │     └─ Model: openai/gpt-4o-mini            │
  │     └─ Prompt: [View] [Edit]                │
  │     └─ Temperature: 0.7                     │
  │                                             │
  │  3️⃣ SMC Analysis                            │
  │     └─ Model: openai/gpt-4o-mini            │
  │     └─ Prompt: [View] [Edit]                │
  │     └─ Temperature: 0.7                     │
  │                                             │
  │  ... (all steps)                            │
  │                                             │
  │  6️⃣ Merge & Telegram Post                    │
  │     └─ Model: openai/gpt-4o-mini             │
  │     └─ Prompt: [View] [Edit]                │
  │     └─ Temperature: 0.7                    │
  └─────────────────────────────────────────────┘
  ```
  
- **Step Configuration Panel** (expandable)
  - For each step:
    - **LLM Model**: Dropdown (from Settings → Available Models)
    - **System Prompt**: Textarea (editable, with versioning)
    - **User Prompt Template**: Textarea (with variables: `{instrument}`, `{timeframe}`, `{market_data}`)
    - **Temperature**: Slider (0-2)
    - **Max Tokens**: Input field
    - **Tools/Data Sources**: 
      - Checkboxes for available tools
      - Data source selector (if step uses data)
      - Show which adapters are available
  
- **Actions**
  - "Run Analysis" (with instrument/timeframe selector)
  - "Save Configuration" (admin only)
  - "Create Copy" (duplicate for customization)
  - "View History" (all runs of this analysis type)

**Key Features:**
- **Prompt Versioning**: See prompt history, compare versions, rollback
- **Model Switching**: Change model per step, see cost impact
- **Template Variables**: Show available variables in prompts
- **Preview Mode**: See what the prompt will look like with sample data

**User Roles:**
- **Admin**: Can edit prompts, models, save configurations
- **Trader**: Can view configuration, run analyses, but cannot modify prompts

---

### 3. Runs (`/runs`) - Analysis Execution History

**Purpose:** View all analysis runs, filter, search, and access results

**Dashboard View (`/runs`):**
- **Filters Bar**
  - Analysis type dropdown
  - Status filter (all/succeeded/failed/running/queued)
  - Instrument filter
  - Date range picker
  - Search by run ID or instrument
  
- **Runs Table**
  - Columns:
    - ID (link to detail)
    - Analysis Type (link to analysis config)
    - Instrument
    - Timeframe
    - Status (badge with color)
    - Steps Completed (e.g., "4/6")
    - Cost
    - Created At
    - Finished At
    - Actions (View, Publish, Delete)
  
- **Bulk Actions** (admin)
  - Delete selected
  - Export selected
  - Retry failed

**Detail View (`/runs/{id}`):**
- **Run Header**
  - Analysis type name
  - Instrument, timeframe
  - Status badge
  - Cost summary
  - Duration
  
- **Timeline View** (current implementation)
  - Expandable steps with prompts/outputs
  - Real-time updates while running
  
- **Final Telegram Post Preview**
  - Copy button
  - Publish button (if succeeded)
  
- **Actions**
  - "Publish to Telegram"
  - "Copy Post"
  - "Retry" (if failed)
  - "Export" (JSON/PDF)

---

### 4. Schedules (`/schedules`) - Automated Analysis Jobs

**Purpose:** Create and manage scheduled analysis runs

**List View (`/schedules`):**
- **Active Schedules Table**
  - Schedule name
  - Analysis type
  - Instrument/timeframe
  - Schedule (cron expression or human-readable)
  - Next run time
  - Status (active/paused)
  - Last run status
  - Actions (Edit, Pause/Resume, Delete, View History)
  
- **Create Schedule Button** (admin)

**Create/Edit Schedule (`/schedules/new`, `/schedules/{id}/edit`):**
- **Form Fields**
  - Schedule name
  - Analysis type selector
  - Instrument selector
  - Timeframe selector
  - Schedule type:
    - Daily (time picker)
    - Weekly (day + time)
    - Custom cron expression
  - Timezone selector
  - Auto-publish to Telegram (checkbox)
  - Enabled/Disabled toggle
  
- **Preview**
  - Shows next 5 scheduled run times
  - Estimated cost per run

**Schedule History (`/schedules/{id}/history`):**
- List of all runs created by this schedule
- Success/failure rate
- Average cost

---

### 5. Settings (`/settings`) - Configuration Management

**Purpose:** Configure models, data sources, Telegram, user preferences

**Tabbed Interface:**

**Tab 1: LLM Models**
- **Available Models Table**
  - Model name/ID
  - Provider (OpenRouter)
  - Cost per 1K tokens
  - Max tokens
  - Status (available/unavailable)
  - Actions (Set as default, Test)
  
- **Model Routing Rules**
  - Per-analysis-type defaults
  - Per-step overrides
  - Cost optimization settings

**Tab 2: Data Sources**
- **Available Adapters**
  - CCXT (crypto exchanges)
    - Exchange selector (Binance, Coinbase, etc.)
    - API keys (if needed)
    - Rate limits
  - yfinance (equities)
    - Market selector (US, EU, etc.)
  - Custom adapters (future)
  
- **Cache Settings**
  - TTL per data source
  - Cache size limits

**Tab 3: Telegram**
- **Bot Configuration**
  - Bot token input
  - Channel ID input
  - Test connection button
  
- **Publishing Settings**
  - Auto-publish on completion (global)
  - Message splitting options
  - Retry policy

**Tab 4: User Preferences**
- **Profile**
  - Email
  - Password change
  - Role display
  
- **UI Preferences**
  - Theme (light/dark/auto)
  - Default timezone
  - Date format
  - Notifications

**Tab 5: System** (admin only)
- **Feature Flags**
  - Enable backtesting
  - Enable custom analyses
  - Enable API access
  
- **Cost Limits**
  - Daily cost limit
  - Per-run cost limit
  - Alerts

---

### 6. Backtesting (`/backtesting`) - Phase 2

**Purpose:** Run analyses on historical data

**List View:**
- Backtest jobs table
- Results comparison

**Create Backtest:**
- Analysis type selector
- Instrument/timeframe
- Date range picker
- Historical data source

---

## User Roles & Permissions

### Admin
- Full access to all features
- Can edit analysis configurations (prompts, models)
- Can create/edit schedules
- Can manage users
- Can configure system settings

### Trader
- Can view analysis configurations (read-only)
- Can run analyses
- Can view all runs
- Can publish to Telegram
- Cannot modify prompts or system settings

---

## Analysis Type Architecture

### Current: Daystart Analysis
- **ID**: `daystart`
- **Steps**: 6 (Wyckoff, SMC, VSA, Delta, ICT, Merge)
- **Default Config**: BTC/USDT, H1 timeframe
- **Estimated Cost**: ~$0.15-0.20 per run

### Future Analysis Types

**1. Intraday SMC Analysis**
- **ID**: `intraday_smc`
- **Steps**: 3 (SMC only, VSA, Merge)
- **Use Case**: Quick intraday structure analysis
- **Default**: M15 timeframe

**2. Weekly Overview**
- **ID**: `weekly_overview`
- **Steps**: 4 (Wyckoff, SMC, ICT, Merge)
- **Use Case**: Weekly market summary
- **Default**: D1 timeframe

**3. Custom Analysis**
- **ID**: `custom_{user_id}_{name}`
- **Steps**: User-defined
- **Use Case**: User-created analysis pipelines
- **Config**: Saved per user

### Analysis Configuration Schema

```python
{
  "id": "daystart",
  "name": "Daystart Analysis",
  "description": "Full market analysis using 5 methodologies",
  "version": "1.2.0",
  "steps": [
    {
      "step_name": "wyckoff",
      "step_type": "llm_analysis",
      "model": "openai/gpt-4o-mini",
      "system_prompt": "...",
      "user_prompt_template": "...",
      "temperature": 0.7,
      "max_tokens": 2000,
      "tools": [],
      "data_sources": ["market_data"]
    },
    {
      "step_name": "data_fetch",
      "step_type": "data_adapter",
      "adapter": "ccxt",
      "exchange": "binance",
      "instrument": "{instrument}",
      "timeframe": "{timeframe}"
    },
    # ... more steps
  ],
  "default_instrument": "BTC/USDT",
  "default_timeframe": "H1",
  "estimated_cost": 0.18,
  "estimated_duration_seconds": 120
}
```

---

## Data Flow & State Management

### Run Lifecycle

```
QUEUED → RUNNING → SUCCEEDED/FAILED
         ↓
    Steps execute sequentially
    Each step: QUEUED → RUNNING → SUCCEEDED/FAILED
```

### Real-time Updates

- **Polling**: Frontend polls `/api/runs/{id}` every 2s while status is RUNNING/QUEUED
- **Future**: WebSocket/SSE for real-time step updates
- **Optimistic UI**: Show step as "running" immediately when pipeline starts

---

## Design System

### Color Palette
- **Primary**: Blue (#3B82F6) - Actions, links
- **Success**: Green (#10B981) - Completed runs
- **Warning**: Yellow (#F59E0B) - Queued/running
- **Error**: Red (#EF4444) - Failed runs
- **Neutral**: Gray scale for text/backgrounds

### Typography
- **Headings**: Inter, bold
- **Body**: Inter, regular
- **Code/Prompts**: JetBrains Mono, monospace

### Components
- **Status Badges**: Colored pills with icons
- **Step Cards**: Expandable accordions
- **Data Tables**: Sortable, filterable, paginated
- **Forms**: Consistent input styling, validation feedback

---

## Mobile Responsiveness

- **Desktop First**: Full feature set
- **Tablet**: Condensed layouts, collapsible sidebars
- **Mobile**: Stack layouts, bottom navigation, essential features only

---

## Accessibility

- **Keyboard Navigation**: Full keyboard support, focus indicators
- **Screen Readers**: ARIA labels, semantic HTML
- **Color Contrast**: WCAG AA compliant
- **Error Messages**: Clear, actionable feedback

---

## Future Enhancements (Post-MVP)

1. **Research Lab**: Interactive prompt playground
2. **Signal Feed**: Aggregated signals from all analyses
3. **API Access**: REST API for programmatic access
4. **Webhooks**: Notify external systems on completion
5. **Collaboration**: Share analyses with team members
6. **Templates**: Pre-built analysis templates marketplace

---

## Implementation Priority

### MVP (Current Focus)
1. ✅ Home/Dashboard
2. ✅ Runs (list + detail)
3. ✅ Analyses (view configuration)
4. ⏳ Schedules (basic)
5. ⏳ Settings (essential only)

### Phase 2
- Full Analyses configuration UI
- Advanced Settings
- Backtesting

### Phase 3
- Research Lab
- Signal Feed
- API Access

