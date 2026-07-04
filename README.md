# Personal Finance Tracker Agent

**An AI-powered personal finance management system with multi-agent ReACT architecture**

## Project Overview

Full-stack personal finance app combining **FastAPI + MongoDB (Motor) backend**, **React + Zustand + Tailwind frontend**, and **ReACT agents** (GoalPlanner, BudgetMonitor) powered by Google Gemini.

### Key Features
- AI transaction categorization via `FinanceTrackerAgent` (ReACT pattern)
- Budget management with per-category limits and alert thresholds (80%/100%)
- Goal planning with progress tracking and auto-completion
- Spending analytics (trends, category breakdown, velocity, unusual patterns)
- Spending forecasting (next-month, by category, budget suggestions)
- Budget monitoring with threshold alerts and reallocation recommendations
- Report generation (monthly, custom, AI insights)
- In-memory TTL cache for analytics/forecast/budget data

---

## Architecture

```
                         ┌──────────────────────────────┐
                         │     Frontend (React + Vite)   │
                         │   6 Pages, 16 Components     │
                         └──────────┬───────────────────┘
                                    │ REST API (61 endpoints)
                         ┌──────────▼───────────────────┐
                         │      FastAPI Backend          │
                         │  9 Router modules, CORS       │
                         └──────────┬───────────────────┘
                                    │
        ┌───────────────┬───────────┼───────────┬───────────────┐
        │               │           │           │               │
        ▼               ▼           ▼           ▼               ▼
  ┌──────────┐   ┌──────────┐ ┌────────┐ ┌──────────┐   ┌──────────┐
  │  Agent   │   │Analytics │ │ Forecast│ │  Cache   │   │ Alerts   │
  │  Layer   │   │ Engine   │ │  Agent  │ │ Manager  │   │ System   │
  └────┬─────┘   └──────────┘ └────────┘ └──────────┘   └──────────┘
       │
  ┌────┴──────────┬────────────────┐
  │               │                │
  ▼               ▼                ▼
GoalPlanner  BudgetMonitor    FinanceTracker
(ReACT)       (ReACT)       (Categorization)
```

---

## Project Structure

```
Finance-Tracker/
├── backend/                          # Python package (FastAPI)
│   ├── agent/                        # BaseAgent + FinanceTrackerAgent
│   │   ├── agent.py                  # BaseAgent ABC, ReACT loop
│   │   ├── goal_planner_agent.py     # GoalPlannerAgent with GoalPlan helper
│   │   ├── budget_monitor_agent.py   # BudgetMonitorAgent with 3-tier alerts
│   │   ├── memory.py                 # AgentMemory
│   │   ├── tools.py                  # Validation/categorization tools
│   │   └── schemas.py                # Agent-specific pydantic models
│   ├── alerts/
│   │   └── alert_system.py           # AlertSystem (current/history/summary)
│   ├── analytics/
│   │   ├── analyzer.py               # AnalyticsEngine (trends, breakdown, velocity)
│   │   ├── forecaster.py             # ForecasterAgent (forecasting, suggestions)
│   │   ├── smart_agent.py            # SmartAgent (AI insights via Gemini)
│   │   ├── goal_planner.py           # GoalPlannerAgent (async MongoDB version)
│   │   └── budget_monitor.py         # BudgetMonitorAgent (async MongoDB version)
│   ├── cache/
│   │   └── cache_manager.py          # TTL CacheManager (analytics/forecast/budget)
│   ├── database/
│   │   └── mongo.py                  # Motor MongoDB connection (connect_db, get_db)
│   ├── migration/
│   │   └── migrate_data.py           # Phase 1 -> Phase 2 data migration
│   ├── models/
│   │   ├── transaction.py            # TransactionInput/Update/Response schemas
│   │   ├── goal.py                   # GoalInput/Update schemas
│   │   └── budget.py                 # BudgetInput schema + DEFAULT_BUDGET_CATEGORIES
│   ├── reports/
│   │   └── report_generator.py       # ReportGenerator (monthly/custom/insights)
│   ├── routes/
│   │   ├── transaction_routes.py     # 10 transaction CRUD endpoints
│   │   ├── agent_routes.py           # 2 agent status/reset endpoints
│   │   ├── budget_routes.py          # 13 budget endpoints
│   │   ├── analytics_routes.py       # 9 analytics endpoints
│   │   ├── forecast_routes.py        # 5 forecast endpoints
│   │   ├── goal_routes.py            # 10 goal endpoints
│   │   ├── budget_monitor_routes.py  # 3 budget-monitor endpoints
│   │   ├── alert_routes.py           # 4 alert endpoints
│   │   └── report_routes.py          # 3 report endpoints
│   ├── main.py                       # FastAPI app (lifespan, CORS, 9 routers)
│   ├── database.py                   # Standalone CRUD (goals_db, budgets_db dicts)
│   ├── schemas.py                    # Root schemas (Goal, Budget models)
│   └── seed_data.py                  # 58 seed transactions
├── agent/                            # Root-level ReACT agents
│   ├── __init__.py
│   ├── goal_planner_agent.py
│   └── budget_monitor_agent.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GoalCard.jsx          # Progress bar, quick-add, delete
│   │   │   ├── GoalList.jsx          # Grid with filter tabs (all/active/completed)
│   │   │   ├── GoalForm.jsx          # Create/edit goal form
│   │   │   ├── GoalDashboard.jsx     # Goal analytics dashboard
│   │   │   ├── BudgetCard.jsx        # Color-coded status, progress bar
│   │   │   ├── BudgetList.jsx        # Month selector, total stats
│   │   │   ├── BudgetForm.jsx        # Create/edit budget form
│   │   │   ├── BudgetDashboard.jsx   # PieChart + BarChart + alerts
│   │   │   ├── BudgetSetup.jsx       # Budget configuration
│   │   │   ├── BudgetTracking.jsx    # Budget tracking view
│   │   │   ├── TransactionForm.jsx   # Add transaction form
│   │   │   ├── TransactionsList.jsx  # Transaction table/list
│   │   │   ├── SummaryDashboard.jsx  # Financial summary
│   │   │   ├── ChartsSection.jsx     # Analytics charts
│   │   │   ├── AlertNotifications.jsx # Alert display
│   │   │   ├── AgentStatus.jsx       # Agent status panel
│   │   │   ├── Layout.jsx            # App layout wrapper
│   │   │   └── Toast.jsx             # Notification toasts
│   │   ├── pages/
│   │   │   ├── HomePage.jsx          # Dashboard (TransactionForm + Summary + Charts)
│   │   │   ├── GoalsPage.jsx         # Goals (GoalList + GoalDashboard)
│   │   │   ├── BudgetPage.jsx        # Budget (BudgetDashboard + BudgetList)
│   │   │   ├── TransactionsPage.jsx  # Transaction history
│   │   │   ├── AlertsPage.jsx        # Alert management
│   │   │   └── AgentPage.jsx         # Agent control panel
│   │   ├── api/client.js             # 37 API methods (fetch-based)
│   │   ├── store/index.js            # Zustand store (transactions, goals, budgets)
│   │   ├── constants/index.js        # Categories, colors, labels, statuses
│   │   └── utils/index.js            # Utility functions
│   └── package.json
├── agent.py                          # Original FinanceTrackerAgent (Phase 1)
├── database.py                       # Original MockDatabase (Phase 1)
├── schemas.py                        # Original schemas (Phase 1)
├── memory.py                         # Original memory (Phase 1)
├── tools.py                          # Original tools (Phase 1)
├── main.py                           # Original main (Phase 1)
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB (optional, app starts without it)
- Google Gemini API Key (optional, agents work without it)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Optional: cp .env.example .env and set GEMINI_API_KEY
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Running
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn backend.main:app --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## API Endpoints (61 total)

### Transactions — `api/transactions` (10)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/transactions/add` | Add transaction (AI-categorized) |
| GET | `/api/transactions/all` | List all transactions |
| GET | `/api/transactions/search?q=` | Search by description/category |
| GET | `/api/transactions/date-range?start_date=&end_date=` | Filter by date range |
| GET | `/api/transactions/category/{category}` | Filter by category |
| GET | `/api/transactions/status/{status}` | Filter by status |
| GET | `/api/transactions/stats` | Aggregate stats by category |
| GET | `/api/transactions/{id}` | Get single transaction |
| PUT | `/api/transactions/{id}` | Update transaction |
| DELETE | `/api/transactions/{id}` | Delete transaction |

### Agent — `/api/agent` (2)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agent/status` | FinanceTrackerAgent state |
| POST | `/api/agent/reset` | Reset agent memory |

### Budget — `/api/budget` (13)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/budget/set` | Set monthly budget (multi-category) |
| POST | `/api/budget/create` | Create per-category budget |
| GET | `/api/budget/current` | Current month budget (cached) |
| GET | `/api/budget/user/{user_id}` | User budgets (current month) |
| GET | `/api/budget/user/{id}/{month}` | User budgets by month |
| GET | `/api/budget/history` | All budget records |
| GET | `/api/budget/{budget_id}` | Single budget |
| PUT | `/api/budget/{budget_id}` | Update budget limit |
| DELETE | `/api/budget/{budget_id}` | Delete budget |
| GET | `/api/budget/vs-actual?month=` | Budget vs actual spending |
| POST | `/api/budget/suggest` | ForecasterAgent suggestions |
| POST | `/api/budget/check-alerts` | Check 80%/100% threshold alerts |
| POST | `/api/budget/monitor` | Full BudgetMonitorAgent run |

### Analytics — `/api/analytics` (9)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/spending-trend?days=` | Daily spending trend |
| GET | `/api/analytics/category-breakdown?month=` | Category breakdown |
| GET | `/api/analytics/spending-velocity` | Spending velocity |
| GET | `/api/analytics/unusual-spending` | Unusual transaction detection |
| GET | `/api/analytics/monthly-comparison?months=` | Month-over-month comparison |
| GET | `/api/analytics/top-days?days=` | Top spending days |
| GET | `/api/analytics/recurring` | Recurring spending patterns |
| GET | `/api/analytics/savings-rate?month=&income=` | Savings rate calc |
| GET | `/api/analytics/budget-vs-actual?month=` | Budget vs actual (analytics) |

### Forecast — `/api/forecast` (5)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/forecast/next-month?history_months=` | Next month forecast |
| GET | `/api/forecast/category/{category}?months=` | Category forecast |
| GET | `/api/forecast/total?days=` | Total spending prediction |
| GET | `/api/forecast/trends` | Spending trend identification |
| POST | `/api/forecast/budget-suggestions` | Budget adjustment suggestions |

### Goals — `/api/goals` (10)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/goals/create` | Create goal |
| GET | `/api/goals/all` | List all goals |
| GET | `/api/goals/active` | List active goals |
| GET | `/api/goals/{goal_id}` | Get single goal |
| PUT | `/api/goals/{goal_id}` | Update goal |
| DELETE | `/api/goals/{goal_id}` | Delete goal |
| GET | `/api/goals/progress/summary` | GoalPlannerAgent progress summary |
| POST | `/api/goals/plan?goal_id=` | Generate savings plan |
| POST | `/api/goals/{id}/add-progress` | Add progress (auto-completes) |
| POST | `/api/goals/analyze` | ReACT GoalPlannerAgent analysis |

### Budget Monitor — `/api/budget-monitor` (3)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/budget-monitor/thresholds` | Budget thresholds |
| GET | `/api/budget-monitor/patterns` | Spending pattern analysis |
| GET | `/api/budget-monitor/recommendations` | Reallocation recommendations |

### Alerts — `/api/alerts` (4)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/alerts/current` | Current alerts |
| GET | `/api/alerts/summary` | Alert summary stats |
| GET | `/api/alerts/history` | Alert history |
| DELETE | `/api/alerts/{alert_id}` | Dismiss alert |

### Reports — `/api/reports` (3)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports/monthly?month=` | Monthly financial report |
| GET | `/api/reports/custom?start_date=&end_date=` | Custom date range report |
| GET | `/api/reports/insights?period=` | AI-generated insights |

---

## Agent Architecture (ReACT Pattern)

### BaseAgent (`backend/agent/agent.py`)
Abstract base class implementing:
- **`register_tool(name, func)`** — register Python functions as agent tools
- **`think(prompt)`** — reasoning step (uses Gemini SDK or fallback)
- **`act(tool_name, **kwargs)`** — execute a registered tool
- **`observe(result)`** — process tool output
- **`react_loop(prompt, max_steps=10)`** — full ReACT loop
- **`get_memory() / clear_memory()`** — memory management

### FinanceTrackerAgent
Extends `BaseAgent`. Validates and categorizes transactions. Used by `POST /api/transactions/add`.

### GoalPlannerAgent (`backend/agent/goal_planner_agent.py`)
4 tools: `analyze_spending`, `calculate_savings`, `suggest_goals`, `create_action_plan`. `GoalPlan` helper class with `monthly_needed`, `priority`, `timeline` properties. Prints `[ANALYZE] [SAVINGS] [GOALS] [PLAN] [PROCESS] [DONE]` debug output.

### BudgetMonitorAgent (`backend/agent/budget_monitor_agent.py`)
4 tools: `check_status`, `analyze_velocity`, `generate_alerts`, `suggest_adjustments`. 3-tier alerts: critical (>=100%), warning (>=80%), ok. Reads real data from `database.py` standalone functions.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python 3.9+) |
| Database | MongoDB via Motor (async), falls back gracefully |
| AI/LLM | Google Gemini 2.5 Flash (optional, graceful fallback) |
| Agent Pattern | ReACT (Reasoning + Acting) |
| Caching | In-memory TTL CacheManager |
| Frontend Framework | React 18 + Vite |
| State Management | Zustand |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Icons | lucide-react |
| HTTP Client | Native fetch (no Axios) |
| Path Alias | `@/` maps to `src/` |

---

## State of Completion

| Step | Component | Status |
|------|-----------|--------|
| 1 | Pydantic schemas (Goal, Budget models) | Complete |
| 2 | Database CRUD (standalone + MongoDB) | Complete |
| 3 | Multi-agent ReACT system (3 agents) | Complete |
| 4 | FastAPI routes (61 endpoints across 9 routers) | Complete |
| 5 | React components (16 components, 6 pages) | Complete |
| 6 | Frontend-backend integration (37 API methods) | Complete |

---

## Testing

```bash
# Verify agents import and run
python -c "from backend.agent import GoalPlannerAgent, BudgetMonitorAgent; print('Agents OK')"

# Start backend
python -m uvicorn backend.main:app --port 8000

# Frontend build
cd frontend && npm run build
```
