<p align="center">
  <h1 align="center">Testcase Executor.AI</h1>
  <p align="center"><strong>Write Test Cases in Plain English — AI Executes Them in a Real Browser</strong></p>
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

**Testcase Executor.AI** lets QA engineers perform automated browser testing by writing test cases in **plain English** inside `.txt` or `.md` files.

**No Playwright syntax. No CSS selectors. No JavaScript. No API key required.**

A built-in **direct rule-based step mapper** converts plain English into Playwright browser actions instantly — with 19 regex patterns and intelligent heuristic fallback. Groq AI is available as an optional enhancement for complex or ambiguous steps.

Upload a file → steps are parsed and mapped → Playwright executes on a **real Chromium browser** (headed or headless) → screenshots captured on every step → real-time progress via SSE → results on the dashboard.

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
- **Direct Step Mapper** — 19 regex patterns convert plain English into Playwright actions with zero AI dependency; heuristic fallback handles any remaining steps
- **Headed / Headless Mode Toggle** — Choose **Headed Mode** to watch the browser live, or **Headless Mode** to run silently in the background
- **Optional AI Enhancement** — Groq LLM as fallback for steps the direct mapper can't resolve (optional, not required)
- **Two-Step Upload** — Select file → preview → click "Upload & Parse" for controlled upload
- **Real-Time Progress** — SSE-powered live events with event replay for late subscribers + 1.5s REST polling fallback guarantees completion detection
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
| Verify text | `Verify that the Dashboard page is displayed` |
| Verify NOT visible | `Verify that error is not displayed` |
| Verify text exact | `Verify error message text is Invalid credentials` |
| Verify URL | `Verify URL contains dashboard`, `Verify URL is https://...` |
| Verify title | `Verify title contains Dashboard` |
| Verify element | `Verify the Login button is visible` |
| Select dropdown | `Select Option 1 from the dropdown` |
| Check/Uncheck | `Check the terms checkbox` |
| Press key | `Press Enter` |
| Wait | `Wait 3 seconds`, `Wait for the spinner to appear` |
| Hover | `Hover over the menu` |
| Scroll | `Scroll to the footer` |
| Refresh/Back | `Refresh the page`, `Go back` |
| Clear | `Clear the search field` |

### Dashboard & Analytics
- **Execution Selector Dropdown** — Switch between executions via top dropdown; all KPI cards and charts scope to the selected run
- 6 KPI cards per execution: Total TCs, Executed, Pending, Passed, Failed, Blocked — each with percentage and contextual metric
- Execution summary panel: file, status, duration, start/completion timestamps
- 3 charts: Status distribution donut, Module-wise bar chart, Test case status breakdown
- **Module-wise Breakdown Table** — Per-module totals with pass/fail/pending/blocked counts and pass rates

### Execution History
- Paginated table (10 per page) with all key columns
- **View Details** (eye icon) — Drill into step-level results with expand/collapse test cases
- **Re-run** (refresh icon) — Creates a new execution from the same file content, runs immediately
- **Delete** (trash icon) — Confirmation-guarded deletion of execution + cascaded test cases, steps, and screenshots

### Execution Detail Page
- Test case expand/collapse with step-by-step results
- Inline screenshot preview per step (modal popup)
- Duration and error details for each step
- **CSV Export** — Download full execution report from detail page or completion popup
- CSV includes: test case names, modules, step descriptions, intents, targets, values, statuses, durations, error messages

### Screenshots & Traceability
- Automatic PNG screenshot after **every step** (pass or fail)
- Screenshot gallery grouped by execution on dedicated page
- Modal preview with full-size view and download button
- Bulk "Delete All" per execution with confirmation dialog
- Single screenshot delete
- Authenticated serving via query-param token (works with browser `<img>` tags)

### AI Configuration (Optional)
- Save/test/delete Groq API key per user
- Model selector dropdown (llama-3.3-70b-versatile, mixtral, gemma, etc.)
- Masked key preview and connection test
- Fernet-encrypted storage with resilient key handling

### Security
- JWT-based authentication (bcrypt password hashing)
- Fernet-encrypted Groq API key storage (auto-generates valid key if config is broken)
- User-scoped data access on all endpoints
- SSE auth via query parameter (required for browser `EventSource` API)
- Screenshot image serving via query-param token (required for browser `<img>` tags)
- Download endpoint supports dual auth: query-param for `<a>` tags, Bearer header for Axios blob downloads
- Passwords and API keys never appear in logs or API responses

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router 6, Recharts, Axios, Lucide React |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), SQLite/aiosqlite, Pydantic v2 |
| **Auth** | JWT (python-jose), bcrypt (passlib), query-param fallback for SSE & images |
| **Step Mapping** | Regex-based direct mapper (19 patterns, 9 locator strategies) + heuristic fallback — no AI required |
| **AI (Optional)** | Groq API (default: `llama-3.3-70b-versatile`) |
| **Browser Automation** | Playwright for Python (async), Chromium headed/headless, Windows ProactorEventLoop |
| **Real-Time** | Server-Sent Events (SSE) with event replay + REST polling fallback (1.5s interval) |
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
│   ├── requirements.txt              # Python dependencies
│   ├── testcase_executor.db          # SQLite database (auto-created)
│   ├── screenshots/                  # Captured screenshot images
│   └── app/
│       ├── main.py                   # FastAPI entry + Windows event loop fix + lifespan
│       ├── config.py                 # Pydantic settings from .env
│       ├── database.py               # Async SQLAlchemy engine + session factory
│       ├── auth/
│       │   ├── models.py             # User model
│       │   ├── schemas.py            # Register/Login/Token schemas
│       │   ├── router.py             # POST /register, /login, GET /me
│       │   ├── service.py            # Business logic (create user, authenticate)
│       │   └── utils.py              # JWT, bcrypt, query-param + header dual auth for SSE, images & downloads
│       ├── models/
│       │   ├── api_key.py            # Encrypted Groq key per user
│       │   └── execution.py          # Execution, TestCase, TestStep, Screenshot models
│       ├── schemas/
│       │   ├── execution.py          # Pydantic CRUD models + ExecutionModeRequest
│       │   └── dashboard.py          # Stats, ModuleStat, DailyTrend
│       ├── routers/
│       │   ├── files.py              # POST /upload — file validation + parse
│       │   ├── executions.py         # CRUD + execute + rerun + delete + export + SSE stream
│       │   ├── dashboard.py          # /stats, /module-stats, /trend, /execution/{id}
│       │   ├── screenshots.py        # List, serve (query-param auth), download, delete single/bulk
│       │   └── ai_config.py          # Groq key management (save/test/delete)
│       └── services/
│           ├── parser.py             # Regex test file parser (33 action verbs, auto-fallback, "Test Case:" headers)
│           ├── step_mapper.py        # Direct rule-based step-to-action engine (19 patterns + heuristic)
│           ├── ai_planner.py         # Groq API planner (optional fallback)
│           ├── playwright_service.py # PlaywrightExecutor + SSEManager with event replay
│           └── encryption.py         # Fernet encrypt/decrypt (resilient to invalid keys)
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                    # SPA routing + API proxy
│   ├── package.json
│   ├── vite.config.ts                # Dev proxy to backend :8000
│   └── src/
│       ├── main.tsx                  # Root: BrowserRouter + App
│       ├── App.tsx                   # 8 routes (login, signup, dashboard, execute, history, detail, screenshots, ai-config)
│       ├── api/client.ts             # Axios with auth interceptors (token injection, 401 redirect)
│       ├── types/index.ts            # 15 TypeScript interfaces
│       ├── hooks/useSSE.ts           # SSE + polling fallback + done detection + reset
│       ├── contexts/AuthContext.tsx   # Auth state + localStorage + loading guard (tri-state)
│       ├── pages/
│       │   ├── LoginPage.tsx          # Username/email + password login
│       │   ├── SignupPage.tsx         # Registration with validation
│       │   ├── DashboardPage.tsx      # Execution selector dropdown + 6 KPI cards + 3 charts + module table
│       │   ├── TestExecutionPage.tsx   # Upload → Parse → Browser Mode → Execute → Live Progress → Complete
│       │   ├── ExecutionHistoryPage.tsx # Paginated table with view/re-run/delete actions
│       │   ├── ExecutionDetailPage.tsx  # Step drill-down + inline screenshots + CSV export
│       │   ├── ScreenshotsPage.tsx      # Gallery grouped by execution + modal preview + bulk delete
│       │   └── AIConfigPage.tsx         # Groq key save/test/delete + model selector
│       └── components/
│           ├── Layout/               # Navbar (Dashboard, Test Execution, History, Screenshots, AI Config) + ProtectedRoute (auth gate)
│           ├── Common/               # ErrorBoundary, Loading, Modal, ConfirmModal, StatusBadge, Toast
│           ├── Dashboard/            # KPICard + Charts (Donut, Bar, Module table)
│           └── Execution/            # FileUpload, TestCasePreview, ExecutionProgress, ExecutionConsole, CompletionPopup
│
└── test-data/
    ├── sample_login_test.md          # 2 test cases with modules/priorities/environment metadata
    ├── sample_login_test.txt         # Plain text single test case
    ├── plain_steps_only.txt          # No header — auto-creates test case from bare steps
    └── test_assertions.txt           # 2 test cases targeting local app (valid + invalid login)
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

# Virtual environment (Windows)
python -m venv venv
venv\Scripts\activate
# Virtual environment (Linux/macOS)
python -m venv venv
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
Go to **AI Config** → enter your Groq API key → click **Save** → click **Test**.

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
Verify URL contains dashboard
Verify title contains Dashboard
Verify the error message is not displayed
```

**No header needed** — even bare steps work:
```text
Open https://example.com
Click the Login button
Verify that Welcome is displayed
```

**Multiple test cases in one file** — just repeat the `Test Case:` header:
```text
Test Case: Valid Login
Open https://example.com/login
...

Test Case: Invalid Login
Open https://example.com/login
...
```

### 4. Upload & Execute
Go to **Test Execution** → drag & drop or browse to select your file → click **Upload & Parse** → choose **Headed Mode** or **Headless Mode** → click **Test Execute**.

- **Headed Mode** — Chromium browser window opens and executes each step live. Watch the progress bar, console log, and completion popup.
- **Headless Mode** — Execution runs silently in the background. Useful for CI/CD or headless servers.

### 5. View Results
- **Dashboard** — Select an execution from the dropdown; KPI cards, charts, and module breakdown scope to that run
- **History** — Paginated table with re-run (🔄) and delete (🗑️) options; click eye icon (👁) for full detail
- **Execution Detail** — Expand test cases, view step-level results with inline screenshot preview
- **Screenshots** — Thumbnail gallery grouped by execution with modal preview, download, and bulk delete
- **CSV Export** — Download from completion popup or Execution Detail page

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | None | Register new user (full_name, username, email, password, confirm_password) |
| `POST` | `/api/v1/auth/login` | None | Login, get JWT token (username_or_email, password) |
| `GET` | `/api/v1/auth/me` | Bearer | Get current user profile |

### Files
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/files/upload` | Bearer | Upload & parse `.txt`/`.md` test file (multipart `file`) |

### Executions
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/executions` | Bearer | Create execution record |
| `POST` | `/api/v1/executions/{id}/execute` | Bearer | Start test execution (`{headless: bool}` in body) |
| `POST` | `/api/v1/executions/{id}/rerun` | Bearer | Re-run from stored file content, creates new execution |
| `GET` | `/api/v1/executions` | Bearer | List executions (paginated: `?page=1&page_size=20`) |
| `GET` | `/api/v1/executions/{id}` | Bearer | Get full execution detail with test cases, steps, and screenshots |
| `GET` | `/api/v1/executions/{id}/stream` | Query (`?token=`) | SSE stream for live execution progress |
| `GET` | `/api/v1/executions/{id}/export` | Bearer | Download CSV execution report |
| `DELETE` | `/api/v1/executions/{id}` | Bearer | Delete execution (cascades to test cases, steps, screenshots) |

### Dashboard
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/dashboard/stats` | Bearer | Aggregate stats across all user executions |
| `GET` | `/api/v1/dashboard/module-stats` | Bearer | Module-wise stats across all executions |
| `GET` | `/api/v1/dashboard/trend` | Bearer | 30-day daily execution trend |
| `GET` | `/api/v1/dashboard/execution/{id}` | Bearer | Per-execution detailed stats with module breakdown |

### Screenshots
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/screenshots` | Bearer | List screenshots (`?execution_id=`) |
| `GET` | `/api/v1/screenshots/{execId}/{stepId}` | Query (`?token=`) | Serve screenshot image (for `<img>` tags) |
| `GET` | `/api/v1/screenshots/download/{id}` | Query/Bearer | Download screenshot (dual auth: query-param + Bearer) |
| `DELETE` | `/api/v1/screenshots/{id}` | Bearer | Delete single screenshot |
| `DELETE` | `/api/v1/screenshots/execution/{execId}` | Bearer | Delete all screenshots for an execution |

### AI Config
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/ai-config` | Bearer | Get AI config (provider, model, masked key preview) |
| `POST` | `/api/v1/ai-config` | Bearer | Save Groq API key + model (`{api_key, model}`) |
| `POST` | `/api/v1/ai-config/test` | Bearer | Test Groq connection (`{api_key, model}`) |
| `DELETE` | `/api/v1/ai-config` | Bearer | Deactivate stored API key |

### Health
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
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
| `FERNET_KEY` | (auto-generated if invalid) | Encryption key for stored API keys |

---

## Architecture Notes

### Headed & Headless Mode Toggle
Users choose the execution mode per run on the Test Execution page:
- **Headed Mode** (`headless: false`) — Playwright launches a visible Chromium window for live observation
- **Headless Mode** (`headless: true`) — Playwright runs in the background with same screenshots, logs, and results

### Direct Step Mapper
The `step_mapper.py` service uses 19 ordered regex patterns (most-specific to most-generic) to convert plain English into Playwright actions. Supports multiple syntax variants, handles numbered steps, strips leading articles, normalizes common field names, and includes a comprehensive heuristic fallback for any unmatched step. **No AI required** — the app works fully offline for all supported patterns.

9 locator strategies: role, label, placeholder, text, alt, title, testid, css — with intelligent strategy selection based on element type (buttons/links → role, form fields → placeholder, generic → text).

### Test Case Parser
The `parser.py` auto-detects test cases from headers (`Test Case:`, `Scenario:`, `TC:`), extracts metadata (Module, Priority, Environment, Browser), and handles bare steps without headers by auto-creating a default test case. Supports 33 action verbs and numbered step formats.

### Windows Event Loop
Playwright requires spawning a browser subprocess, which the default `SelectorEventLoop` on Windows can't handle. The app automatically switches to `WindowsProactorEventLoopPolicy` at startup via `main.py`.

### SSE with Polling Fallback
Browsers' `EventSource` API can't send custom headers, so SSE auth flows through `?token=` query parameters. The `get_current_user_from_query` dependency handles this securely. The frontend's `useSSE` hook also polls `GET /executions/{id}` every 1.5 seconds — if execution completes before the SSE connection opens, the REST status check injects the completion event.

### SSE Event Replay
The `SSEManager` stores event history per execution. Late-connecting SSE clients receive all past events replayed before live events begin. Queues persist for 30 seconds after completion.

### Screenshot Authentication
Browser `<img>` tags cannot send `Authorization` headers, so screenshot image URLs include a `?token=` query parameter. The backend uses `get_current_user_from_query` to authenticate these requests. The download endpoint supports **dual authentication**: query-param tokens (for `<a>` tag direct downloads) and `Authorization: Bearer` headers (for Axios blob downloads via the frontend's auth interceptor). The `/download/{id}` route is registered before `/{execution_id}/{step_id}` in FastAPI to prevent route shadowing.

### Fernet Key Resilience
If the `FERNET_KEY` in `.env` is invalid, the encryption service auto-generates a valid key at runtime instead of crashing. A warning is logged when decryption fails due to key mismatch.

### Fail-Fast Per Test Case
If a step fails, remaining steps in that test case are marked `SKIPPED`, but subsequent test cases continue to execute.

### Auth Loading Guard (Tri-State)
The `AuthContext` uses a `loading` flag that starts `true` when a stored token exists. `ProtectedRoute` blocks route evaluation until the `/auth/me` validation call settles via `.finally()`, preventing false-negative auth gaps on page refresh.

---

## Troubleshooting

### Browser doesn't open
- Ensure Playwright browsers are installed: `playwright install chromium`
- On WSL/Linux headless servers, use **Headless Mode** or set up a virtual display with `xvfb-run`
- For Docker on Linux, mount the X11 socket or use VNC (or use Headless Mode)
- **Windows:** The ProactorEventLoop is set automatically — if you still see `NotImplementedError`, ensure you're running `app.main:app` (not a custom entry point)

### Groq API errors
- The app works without Groq for supported step patterns. Only unmapped steps require it.
- Verify your API key is correct in **AI Config**
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
