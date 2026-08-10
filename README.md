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
- [Architecture Notes](#architecture-notes)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Testcase Executor.AI** lets QA engineers and developers perform automated browser testing by writing test cases in **plain English** inside `.txt` or `.md` files.

**No Playwright syntax. No CSS selectors. No JavaScript. No API key required.**

A built-in **direct rule-based step mapper** converts plain English into Playwright browser actions instantly. Groq AI is available as an optional fallback for complex or ambiguous steps.

Upload a file → steps are parsed and mapped → Playwright executes on a **real Chromium browser** that you can **watch live** or run **headless in the background** → screenshots captured on every step → results on the dashboard.

---

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Write test  │────▶│  Upload .txt │────▶│ Direct step  │────▶│ Playwright   │
│  in English  │     │  or .md file │     │  mapper or   │     │ executes in  │
│              │     │  + click     │     │  Groq (opt)  │     │ headed /     │
│              │     │  Upload btn  │     │              │     │ headless mode│
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
- **Direct Step Mapper** — 19 regex patterns convert plain English into Playwright actions with zero AI dependency
- **Headed / Headless Mode Toggle** — Choose **Headed Mode** to watch the browser live, or **Headless Mode** to run silently in the background
- **Optional AI Enhancement** — Groq LLM as fallback for steps the direct mapper can't resolve
- **Two-Step Upload** — Select file → preview → click "Upload & Parse" for controlled upload
- **Real-Time Progress** — SSE-powered live events + 1.5s polling fallback guarantees completion detection
- **Progress Bar States** — Shows RUNNING during execution, COMPLETED with green banner when done

### Direct Mapper — Supported Step Patterns
| Pattern | Example |
|---------|---------|
| Navigate / Login | `Open https://example.com/login`, `Login to https://example.com` |
| Type/Input (quoted) | `Enter "john@example.com" in the username field` |
| Type/Input (as syntax) | `Enter the user name as standard_user` |
| Type/Input (unquoted) | `Enter john in the username field` |
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
- Automatic PNG screenshot after **every step** (pass or fail)
- Thumbnail gallery grouped by execution
- Modal preview with full-size view and download button
- Authenticated serving via query-param token (works with browser `<img>` tags)

### Export
- **CSV Export** — Download execution reports with summary and per-step detail from Completion popup or Execution Detail page
- Report includes: test case names, modules, step descriptions, intents, targets, statuses, durations, error messages

### Security
- JWT-based authentication (bcrypt password hashing)
- Fernet-encrypted Groq API key storage (auto-generates valid key if config is broken)
- User-scoped data access on all endpoints
- SSE auth via query parameter (required for browser `EventSource` API)
- Screenshot image serving via query-param token (required for browser `<img>` tags)

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
| **Auth** | JWT (python-jose), bcrypt (passlib), query-param fallback for SSE & images |
| **Step Mapping** | Regex-based direct mapper (19 patterns, 9 locator strategies) — no AI required |
| **AI (Optional)** | Groq API (default: `llama-3.3-70b-versatile`) |
| **Browser Automation** | Playwright for Python (async), Chromium headed/headless, Windows ProactorEventLoop |
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
│       │   └── utils.py              # JWT, bcrypt, query-param + header dual auth for SSE, images & downloads
│       ├── models/
│       │   ├── api_key.py            # Encrypted Groq key per user
│       │   └── execution.py          # Execution, TestCase, TestStep, Screenshot
│       ├── schemas/
│       │   ├── execution.py          # Pydantic CRUD models + ExecutionModeRequest
│       │   └── dashboard.py          # Stats, ModuleStat, DailyTrend
│       ├── routers/
│       │   ├── files.py              # POST /upload — file validation + parse
│       │   ├── executions.py         # CRUD + execute + rerun + delete + export + SSE
│       │   ├── dashboard.py          # /stats, /module-stats, /trend
│       │   ├── screenshots.py        # List, serve (query-param auth), download
│       │   └── ai_config.py          # Groq key management
│       └── services/
│           ├── parser.py             # Regex test file parser (33 action verbs, auto-fallback)
│           ├── step_mapper.py        # Direct rule-based step-to-action engine (19 patterns)
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
│       │   ├── TestExecutionPage.tsx  # Upload → Parse → Browser Mode → Execute → Complete
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
- **Groq API key** — optional; the app works without it for supported test patterns

### Option 1: Docker (Recommended)

```bash
cd Project34_TestCaseExecutor

# Start both services
docker compose up -d --build

# Open http://localhost:3000
```

> **Note:** Headed browser mode requires a display. On Linux servers, mount `/tmp/.X11-unix` or use VNC. Use Headless Mode for headless servers.

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

> **Skip this step to use the built-in direct step mapper.** The app works without an API key for supported test patterns.

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

**Alternative syntaxes** (all supported):
```text
Enter the user name as standard_user
Enter john@example.com in the username field
Fill the password field with "Password123"
Login to https://example.com
```

**No header needed** — even bare steps work:
```text
Open https://example.com
Click the Login button
Verify that Welcome is displayed
```

### 4. Upload & Execute
Go to **Test Execution** → drag & drop or browse to select your file → click **Upload & Parse** → choose **Headed Mode** or **Headless Mode** → click **Test Execute**.

- **Headed Mode** — Chromium browser window opens and executes each step live. Watch the progress bar, console log, and completion popup.
- **Headless Mode** — Execution runs silently in the background. Useful for CI/CD or headless servers.

### 5. View Results
- **Dashboard** — KPI cards and charts auto-update
- **Execution History** — table with re-run (🔄) and delete (🗑️) options
- **Execution Detail** — expand test cases, view step-level results and inline screenshots
- **Screenshots** — thumbnail gallery with modal preview and download
- **Export** — download CSV reports from the completion popup or detail page

---

## API Reference

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| `POST` | `/api/v1/auth/register` | None | 201 | Register new user |
| `POST` | `/api/v1/auth/login` | None | 200 | Login, get JWT token |
| `GET` | `/api/v1/auth/me` | Bearer | 200 | Get current user |
| `POST` | `/api/v1/files/upload` | Bearer | 200 | Upload & parse test file |
| `POST` | `/api/v1/executions` | Bearer | 200 | Create execution record |
| `POST` | `/api/v1/executions/{id}/execute` | Bearer | 200 | Start test execution (`{headless: bool}`) |
| `POST` | `/api/v1/executions/{id}/rerun` | Bearer | 200 | Re-run execution (`{headless: bool}`) |
| `GET` | `/api/v1/executions` | Bearer | 200 | List executions (paginated: `?page=1&page_size=20`) |
| `GET` | `/api/v1/executions/{id}` | Bearer | 200 | Get execution detail with steps + screenshots |
| `GET` | `/api/v1/executions/{id}/stream` | Query (`?token=`) | 200 | SSE stream for live progress |
| `GET` | `/api/v1/executions/{id}/export` | Bearer | 200 | Download CSV execution report |
| `DELETE` | `/api/v1/executions/{id}` | Bearer | 200 | Delete execution (cascades) |
| `GET` | `/api/v1/screenshots?execution_id=` | Bearer | 200 | List screenshots for execution |
| `GET` | `/api/v1/screenshots/{execId}/{stepId}` | Query (`?token=`) | 200 | Serve screenshot image |
| `GET` | `/api/v1/screenshots/download/{id}` | Query/Bearer | 200 | Download screenshot (supports both `<a>` tag query-param and Axios Bearer header) |
| `DELETE` | `/api/v1/screenshots/{id}` | Bearer | 200 | Delete single screenshot |
| `DELETE` | `/api/v1/screenshots/execution/{id}` | Bearer | 200 | Delete all screenshots for an execution |
| `GET` | `/api/v1/dashboard/stats` | Bearer | 200 | Dashboard statistics |
| `GET` | `/api/v1/dashboard/module-stats` | Bearer | 200 | Module-wise stats |
| `GET` | `/api/v1/dashboard/trend` | Bearer | 200 | 30-day execution trend |
| `GET` | `/api/v1/ai-config` | Bearer | 200 | Get AI configuration |
| `POST` | `/api/v1/ai-config` | Bearer | 200 | Save Groq API key + model |
| `DELETE` | `/api/v1/ai-config` | Bearer | 200 | Delete Groq API key |
| `POST` | `/api/v1/ai-config/test` | Bearer | 200 | Test Groq connection |
| `GET` | `/api/health` | None | 200 | Health check |

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

### Headed & Headless Mode Toggle
Users can choose the execution mode before running a test:
- **Headed Mode** (`headless: false`) — Playwright launches a visible Chromium window. You can watch every click, fill, and navigation in real time.
- **Headless Mode** (`headless: true`) — Playwright runs in the background. The same screenshots, logs, and results are captured without a visible window.

The toggle is on the Test Execution page between file parsing and the "Test Execute" button.

### Direct Step Mapper
The `step_mapper.py` service uses 19 ordered regex patterns to convert plain English into Playwright actions. It supports multiple syntax variants (`Enter "x" in field`, `Enter field as x`, `Enter x in field`), handles numbered steps, strips leading articles ("the", "a", "an"), and normalizes common field names ("user name" → "username", "pass word" → "password").

9 locator strategies: role, label, placeholder, text, alt, title, testid, css — with intelligent strategy selection based on element type (buttons/links → role, form fields → placeholder, generic → text).

### Windows Event Loop
Playwright requires spawning a browser subprocess, which the default `SelectorEventLoop` on Windows can't handle. The app automatically switches to `WindowsProactorEventLoopPolicy` at startup via `main.py`.

### SSE with Polling Fallback
Browsers' `EventSource` API can't send custom headers, so SSE auth flows through `?token=` query parameters. The `get_current_user_from_query` dependency handles this securely. The frontend also polls `GET /executions/{id}` every 1.5 seconds as a fallback — if execution completes before the SSE connection opens, the REST status check injects the completion event.

### SSE Event Replay
The `SSEManager` stores event history per execution. Late-connecting SSE clients receive all past events replayed before live events begin, and queues persist for 30 seconds after completion.

### Screenshot Authentication
Browser `<img>` tags cannot send `Authorization` headers, so screenshot image URLs include a `?token=` query parameter. The backend uses `get_current_user_from_query` to authenticate these requests.

The download endpoint supports **dual authentication**: query-param tokens (for `<a>` tag direct downloads) and `Authorization: Bearer` headers (for Axios `responseType: 'blob'` downloads via the frontend's auth interceptor). The `/download/{id}` route is registered before `/{execution_id}/{step_id}` in FastAPI to prevent route shadowing.

### Fernet Key Resilience
If the `FERNET_KEY` in `.env` is invalid, the encryption service auto-generates a valid key at runtime instead of crashing.

### Fail-Fast Per Test Case
If a step fails, remaining steps in that test case are marked `SKIPPED`, but subsequent test cases continue to execute.

---

## Troubleshooting

### Browser doesn't open
- Ensure Playwright browsers are installed: `playwright install chromium`
- On WSL/Linux headless servers, use **Headless Mode** or set up a virtual display with `xvfb-run`
- For Docker on Linux, mount the X11 socket or use VNC (or use Headless Mode)
- **Windows:** The ProactorEventLoop is set automatically — if you still see `NotImplementedError`, ensure you're running `app.main:app` (not a custom entry point)

### Groq API errors
- The app works without Groq for supported step patterns. Only unmapped steps require it.
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
- Screenshot images require authentication — if logged out, images won't load

### Port conflicts
- Backend (8000): change with `--port` flag or `PORT` env variable
- Frontend (5173): configured in `vite.config.ts`

### Database issues
- Delete `backend/testcase_executor.db` to reset the database
- Tables are auto-created on startup
