<p align="center">
  <h1 align="center">Testcase Executor.AI</h1>
  <p align="center"><strong>Write Test Cases in Plain English — Execute in a Real Browser with Zero AI Configuration</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/react-18-61dafb" alt="React">
  <img src="https://img.shields.io/badge/playwright-1.49-45ba4b" alt="Playwright">
  <img src="https://img.shields.io/badge/no%20AI%20key%20required-success" alt="No AI key">
</p>

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Option 1: Docker (Recommended)](#option-1-docker-recommended)
  - [Option 2: Manual Setup](#option-2-manual-setup)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Testcase Executor.AI** lets QA engineers and developers perform automated browser testing by writing test cases in **plain English** inside `.txt` or `.md` files.

**No Playwright syntax. No CSS selectors. No JavaScript. No API key required.**

A built-in **direct rule-based step mapper** converts plain English into Playwright browser actions instantly. Groq AI is available as an optional fallback for complex or ambiguous steps.

Upload a file → steps are parsed and mapped → Playwright executes on a **real Chromium browser in headed mode** that you can **watch live** → screenshots captured → results on the dashboard.

---

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Write test  │────▶│  Upload .txt │────▶│ Direct step  │────▶│ Playwright   │
│  in English  │     │  or .md file │     │  mapper or   │     │ executes on  │
│              │     │  + click     │     │  Groq (opt)  │     │ real browser │
│              │     │  Upload btn  │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                               ┌───────▼───────┐
                                                               │ Screenshots + │
                                                               │ Live Progress │
                                                               │  + CSV Export │
                                                               └───────────────┘
```

---

## Features

### Core Workflow
- **Plain English Test Cases** — Write in `.txt` or `.md`, no automation knowledge needed
- **Direct Step Mapper** — 18+ regex patterns convert plain English into Playwright actions with zero AI dependency
- **Optional AI Enhancement** — Groq LLM as fallback for steps the direct mapper can't resolve
- **Two-Step Upload** — Select file → preview → click "Upload & Parse" for controlled upload
- **Headed Browser Execution** — Watch Playwright control a real Chromium browser live
- **Real-Time Progress** — SSE-powered live events + 1.5s polling fallback guarantees completion detection
- **Progress Bar States** — Shows RUNNING during execution, COMPLETED with green banner when done

### Direct Mapper — Supported Step Patterns
| Pattern | Example |
|---------|---------|
| Navigate | `Open https://example.com/login` |
| Type/Input | `Enter "john@example.com" in the username field` |
| Fill with | `Fill the password field with "Password123"` |
| Click | `Click the Login button` |
| Double-click | `Double click the Submit button` |
| Verify | `Verify that the Dashboard page is displayed` |
| Select dropdown | `Select Option 1 from the dropdown` |
| Check/Uncheck | `Check the terms checkbox` |
| Press key | `Press Enter` |
| Wait | `Wait 3 seconds`, `Wait for the spinner to disappear` |
| Hover | `Hover over the menu` |
| Scroll | `Scroll to the footer` |
| Refresh/Back | `Refresh the page`, `Go back` |
| Clear | `Clear the search field` |

### Dashboard & Analytics
- 8 KPI cards: Total Executions, Passed, Failed, Running, Blocked, Total Test Cases, Pass %, Fail %
- 3 charts: Pass vs Fail pie chart, Module-wise bar chart, 30-day execution trend
- Execution history with pagination, re-run, and delete
- Drill-down detail view with step-level results and inline screenshot preview

### Screenshots & Traceability
- Automatic PNG screenshot after every step (pass or fail)
- Thumbnail gallery grouped by execution
- Modal preview with full-size view and download button

### Export
- **CSV Export** — Download execution reports with summary and per-step detail from Completion popup or Execution Detail page
- Report includes: test case names, modules, step descriptions, intents, targets, statuses, durations, error messages

### Security
- JWT-based authentication (bcrypt password hashing)
- Fernet-encrypted Groq API key storage (auto-generates valid key if config is broken)
- User-scoped data access on all endpoints
- SSE auth via query parameter (required for browser `EventSource` API)

### AI Configuration (Optional)
- Save/test/delete Groq API key per user
- Model selector dropdown (llama-3.3-70b-versatile, mixtral, gemma, etc.)
- Masked key preview and connection test

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router 6, Recharts, Axios, Lucide React |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), SQLite/aiosqlite, Pydantic v2 |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Step Mapping** | Regex-based direct mapper (18 patterns, 9 locator strategies) — no AI required |
| **AI (Optional)** | Groq API (default: `llama-3.3-70b-versatile`) |
| **Browser Automation** | Playwright for Python (async), Chromium headed mode, Windows ProactorEventLoop |
| **Real-Time** | Server-Sent Events (SSE) with event replay + REST polling fallback |
| **Encryption** | Fernet symmetric encryption (cryptography) — resilient to invalid keys |

---

## Project Structure

```
Project34_TestCaseExecutor/
├── docker-compose.yml
├── README.md                         # This file
├── TestcaseExecutor.md               # Full specification (RICEPOT framework)
├── .env                              # Environment configuration
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt              # 15 Python dependencies
│   ├── testcase_executor.db          # SQLite database (auto-created)
│   ├── screenshots/                  # Captured screenshot images
│   └── app/
│       ├── main.py                   # FastAPI entry + Windows event loop fix
│       ├── config.py                 # Pydantic settings from .env
│       ├── database.py               # Async SQLAlchemy engine
│       ├── auth/
│       │   ├── models.py             # User model
│       │   ├── schemas.py            # Register/Login/Tokens
│       │   ├── router.py             # POST /register, /login, GET /me
│       │   ├── service.py            # Business logic
│       │   └── utils.py              # JWT, bcrypt, query-param auth for SSE
│       ├── models/
│       │   ├── api_key.py            # Encrypted Groq key per user
│       │   └── execution.py          # Execution, TestCase, TestStep, Screenshot
│       ├── schemas/
│       │   ├── execution.py          # Pydantic CRUD models
│       │   └── dashboard.py          # Stats, ModuleStat, DailyTrend
│       ├── routers/
│       │   ├── files.py              # POST /upload — file validation + parse
│       │   ├── executions.py         # CRUD + execute + rerun + delete + export + SSE
│       │   ├── dashboard.py          # /stats, /module-stats, /trend
│       │   ├── screenshots.py        # List, serve, download screenshots
│       │   └── ai_config.py          # Groq key management
│       └── services/
│           ├── parser.py             # Regex test file parser (auto-fallback)
│           ├── step_mapper.py        # Direct rule-based step-to-action engine
│           ├── ai_planner.py         # Groq API planner (optional fallback)
│           ├── playwright_service.py # PlaywrightExecutor + SSE manager with replay
│           └── encryption.py         # Fernet encrypt/decrypt (resilient)
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                    # SPA routing + API proxy
│   ├── package.json
│   ├── vite.config.ts                # Dev proxy to backend :8000
│   └── src/
│       ├── main.tsx                  # Root: BrowserRouter + App
│       ├── App.tsx                   # 8 routes
│       ├── api/client.ts             # Axios with auth interceptors
│       ├── types/index.ts            # 15 TypeScript interfaces
│       ├── hooks/useSSE.ts           # SSE + polling fallback + done detection
│       ├── contexts/AuthContext.tsx   # Auth state + localStorage
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── SignupPage.tsx
│       │   ├── DashboardPage.tsx     # 8 KPI cards + 3 charts
│       │   ├── TestExecutionPage.tsx  # Upload → Parse → Execute → Complete
│       │   ├── ExecutionHistoryPage.tsx # Table with pagination, re-run, delete
│       │   ├── ExecutionDetailPage.tsx # Step drill-down + screenshots + export
│       │   ├── ScreenshotsPage.tsx   # Gallery with modal preview
│       │   └── AIConfigPage.tsx      # Groq key settings
│       └── components/
│           ├── Layout/               # Navbar + ProtectedRoute
│           ├── Common/               # ErrorBoundary, Loading, Modal, StatusBadge, Toast
│           ├── Dashboard/            # KPICard + Charts (Pie, Bar, Line)
│           └── Execution/            # FileUpload, TestCasePreview, Progress,
│                                     # Console, CompletionPopup
│
└── test-data/
    ├── sample_login_test.md          # 2 test cases with modules/priorities
    ├── sample_login_test.txt         # Plain text test case
    └── plain_steps_only.txt          # No header, auto-detect test
```

---

## Getting Started

### Prerequisites

- **Python 3.12+** (for manual setup)
- **Node.js 20+** (for manual setup)
- **Playwright browsers** — install with `playwright install chromium`
- **Docker & Docker Compose** (for Docker setup)
- **Groq API key** — optional; the app works without it for most test patterns

### Option 1: Docker (Recommended)

```bash
cd Project34_TestCaseExecutor

# Start both services
docker compose up -d --build

# Open http://localhost:3000
```

> **Note:** Headed browser mode requires a display. On Linux servers, mount `/tmp/.X11-unix` or use VNC.

Stop services:
```bash
docker compose down
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install
# Note: if vite is missing, run: npm install --include=dev

# Run dev server (proxies /api to backend)
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Usage Guide

### 1. Register & Login
Navigate to `http://localhost:5173` → Sign Up → Login.

### 2. (Optional) Configure Groq API Key
Go to **AI Configuration** → enter your Groq API key → click **Save** → click **Test**.

> **Skip this step to use the built-in direct step mapper.** The app works without an API key for most common test patterns.

### 3. Write Test Cases
Create a `.txt` or `.md` file:

```text
Test Case: Login with valid credentials
Module: Authentication
Priority: High

Open https://example.com/login
Enter "john@example.com" in the username field
Enter "Password123" in the password field
Click the Login button
Verify that the Dashboard page is displayed
```

**No header needed** — even bare steps work:
```text
Open https://example.com
Click the Login button
Verify that Welcome is displayed
```

### 4. Upload & Execute
Go to **Test Execution** → drag & drop or browse to select your file → click **Upload & Parse** → review parsed test cases → click **Test Execute**.

A Chromium browser window opens and executes each step. Watch the progress bar, console log, and completion popup.

### 5. View Results
- **Dashboard** — KPI cards and charts auto-update
- **Execution History** — table with re-run (🔄) and delete (🗑️) options
- **Execution Detail** — expand test cases, view step-level results and inline screenshots
- **Screenshots** — thumbnail gallery with modal preview and download
- **Export** — download CSV reports from the completion popup or detail page

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | None | Register new user |
| `POST` | `/api/v1/auth/login` | None | Login, get JWT token |
| `GET` | `/api/v1/auth/me` | Bearer | Get current user |
| `POST` | `/api/v1/files/upload` | Bearer | Upload & parse test file |
| `POST` | `/api/v1/executions` | Bearer | Create execution record |
| `POST` | `/api/v1/executions/{id}/execute` | Bearer | Start test execution (direct mapper + optional Groq) |
| `POST` | `/api/v1/executions/{id}/rerun` | Bearer | Re-run execution |
| `GET` | `/api/v1/executions` | Bearer | List executions (paginated: `?page=1&page_size=20`) |
| `GET` | `/api/v1/executions/{id}` | Bearer | Get execution detail with steps + screenshots |
| `GET` | `/api/v1/executions/{id}/stream` | Query (`?token=`) | SSE stream for live progress (no Bearer — EventSource limitation) |
| `GET` | `/api/v1/executions/{id}/export` | Bearer | Download CSV execution report |
| `DELETE` | `/api/v1/executions/{id}` | Bearer | Delete execution (cascades: test cases → steps → screenshots) |
| `GET` | `/api/v1/screenshots?execution_id=` | Bearer | List screenshots for execution |
| `GET` | `/api/v1/screenshots/{execId}/{stepId}` | Bearer | Serve screenshot image |
| `GET` | `/api/v1/screenshots/download/{id}` | Bearer | Download screenshot |
| `GET` | `/api/v1/dashboard/stats` | Bearer | Dashboard statistics |
| `GET` | `/api/v1/dashboard/module-stats` | Bearer | Module-wise stats |
| `GET` | `/api/v1/dashboard/trend` | Bearer | 30-day execution trend |
| `GET` | `/api/v1/ai-config` | Bearer | Get AI configuration |
| `POST` | `/api/v1/ai-config` | Bearer | Save Groq API key |
| `DELETE` | `/api/v1/ai-config` | Bearer | Delete Groq API key |
| `POST` | `/api/v1/ai-config/test` | Bearer | Test Groq connection |
| `GET` | `/api/health` | None | Health check |

---

## Configuration

All settings via `.env` file or environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key-change-in-production-32bytes` | JWT signing secret |
| `DATABASE_URL` | `sqlite+aiosqlite:///./testcase_executor.db` | Database connection URL |
| `GROQ_API_KEY` | (empty) | Fallback Groq API key (optional) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Default Groq model |
| `SCREENSHOTS_DIR` | `./screenshots` | Directory for screenshot images |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT token expiry (24 hours) |
| `FERNET_KEY` | (auto-generated) | Encryption key for stored API keys |

---

## Architecture Notes

### Direct Step Mapper
The `step_mapper.py` service uses 18 ordered regex patterns to convert plain English into Playwright actions. It handles the most common test patterns (navigate, type, click, verify, select, wait, hover, scroll, etc.) and picks intelligent locators (role → placeholder → label → text → CSS). Groq AI is only invoked if some steps can't be mapped AND the user has configured a valid API key.

### Windows Event Loop
Playwright requires spawning a browser subprocess, which the default `SelectorEventLoop` on Windows can't handle. The app automatically switches to `WindowsProactorEventLoopPolicy` at startup via `main.py`.

### SSE with Polling Fallback
Browsers' `EventSource` API can't send custom headers, so SSE auth flows through `?token=` query parameters. A `get_current_user_from_query` dependency handles this securely. The frontend also polls `GET /executions/{id}` every 1.5 seconds as a fallback — if execution completes before the SSE connection opens, the REST status check injects the completion event.

### SSE Event Replay
The `SSEManager` stores event history per execution. Late-connecting SSE clients receive all past events replayed before live events begin, and queues persist for 30 seconds after completion.

### Fernet Key Resilience
If the `FERNET_KEY` in `.env` is invalid, the encryption service auto-generates a valid key at runtime instead of crashing.

---

## Troubleshooting

### Browser doesn't open
- Ensure Playwright browsers are installed: `playwright install chromium`
- On WSL/Linux headless servers, set up a virtual display with `xvfb-run`
- For Docker on Linux, mount the X11 socket or use VNC
- **Windows:** The ProactorEventLoop is set automatically — if you still see `NotImplementedError`, ensure you're running `app.main:app` (not a custom entry point)

### Groq API errors
- The app works without Groq for most steps. Only unmapped steps require it.
- Verify your API key is correct in **AI Configuration**
- Click **Test** to verify connectivity

### "No test cases found" on upload
- The parser auto-detects test cases from headers (`Test Case:`, `Scenario:`, `TC:`)
- If no header is present, it auto-creates a test case from orphan steps
- Ensure your file has at least one recognizable step (starts with an action verb or URL)

### Screenshots not showing
- Screenshots are captured after every step execution
- Check `backend/screenshots/` directory for PNG files
- In the Execution Detail page, expand a test case to see step-level screenshots
- The Screenshots page groups thumbnails by execution

### Port conflicts
- Backend (8000): change with `--port` flag or `PORT` env variable
- Frontend (5173): configured in `vite.config.ts`

### Database issues
- Delete `backend/testcase_executor.db` to reset the database
- Tables are auto-created on startup
