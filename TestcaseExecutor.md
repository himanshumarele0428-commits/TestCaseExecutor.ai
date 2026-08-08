# Testcase Executor.AI — Simple English Test Execution Specification

## RICEPOT Framework

### R — Role

You are a Senior AI Test Automation Architect and Full-Stack Developer responsible for building **Testcase Executor.AI**, an AI-powered test execution application.

The core purpose of the application is simple:

> A user writes test steps in plain English inside a `.txt` or `.md` file, uploads the file, and the AI Agent understands those steps and executes them on a real browser using Playwright in the backend.

The user must be able to **watch the browser execution in headed mode**.

The system must prioritize reliable execution, traceability, screenshots, accurate results, and clear reporting.

---

# I — Input

## 1. Test Case Input

The application must accept **ONLY text-based test case files**:

- `.txt`
- `.md`

Do NOT require Excel, CSV, JSON, or any other structured test-case format.

The purpose is to allow a non-technical QA user to write test cases using simple English.

### Example `.txt` file

```text
Test Case: Login with valid credentials

Open https://example.com/login

Enter "john@example.com" in the username field

Enter "Password123" in the password field

Click the Login button

Verify that the Dashboard page is displayed
```

### Example `.md` file

```markdown
# Test Case: Login with valid credentials

1. Open https://example.com/login
2. Enter "john@example.com" in the username field
3. Enter "Password123" in the password field
4. Click the Login button
5. Verify that the Dashboard page is displayed
```

The user should NOT need to know:

- Playwright syntax
- JavaScript/TypeScript
- CSS selectors
- XPath
- Page Object Model
- Automation framework syntax

The AI Agent is responsible for converting natural-language instructions into executable Playwright actions.

---

# C — Context

## 1. Application Name

**Testcase Executor.AI**

## 2. Main Objective

Build an application with this workflow:

```text
User Login
     ↓
Dashboard
     ↓
Upload .TXT / .MD File
     ↓
AI Reads Plain-English Steps
     ↓
AI Understands Test Intent
     ↓
AI Generates Execution Plan
     ↓
Playwright Agent Executes Steps
     ↓
Browser Runs in HEADED Mode
     ↓
User Watches Browser
     ↓
Screenshot After Each Step
     ↓
Step Result
     ↓
Test Case Pass / Fail
     ↓
Execution Report
```

## 3. Important Design Principle

The user provides **instructions, not automation code**.

For example:

```text
Open the login page.

Enter admin@test.com in the username field.

Enter Password123 in the password field.

Click Login.

Verify that the home page is displayed.
```

The AI Agent should internally translate these instructions into Playwright actions.

The user should never be required to write:

```javascript
await page.locator(...).fill(...);
await page.getByRole(...).click();
```

---

# E — Expectation

## 1. User Registration

Create an account page with:

- Full Name
- Username
- Email ID
- Password
- Confirm Password
- Register button

Requirements:

- Validate mandatory fields.
- Validate email.
- Validate password confirmation.
- Prevent duplicate accounts.
- Hash passwords securely.
- Never store plain-text passwords.

---

# 2. User Login

Login page:

- Username/Email
- Password
- Login button

After successful login:

```text
Login → Dashboard
```

Protected pages must not be accessible without authentication.

---

# 3. Dashboard

The dashboard must provide an overview of test execution.

### KPI Cards

Display:

- Total Test Cases
- Total Executed
- Passed
- Failed
- Running
- Blocked
- Pass Percentage
- Fail Percentage

### Graphs

Provide:

1. Pass vs Fail chart
2. Execution status chart
3. Test execution trend
4. Module-wise statistics if modules are defined in the text files

All values must come from actual execution data.

Do not use hard-coded results.

---

# 4. Test Execution Page

Create a page called:

**Test Execution**

The page must provide:

- `.txt` / `.md` upload
- File name
- Test case preview
- Detected test cases
- Test Execute button
- Execution status
- Current test case
- Current step
- Current browser status
- Execution progress

Example:

```text
Uploaded File:
login_test.md

Test Cases Found:
1

Steps Found:
5

[ Test Execute ]
```

---

# 5. Plain-English Test Case Parser

The AI Agent must interpret common natural-language instructions.

Examples:

### Navigation

```text
Open https://example.com
Go to https://example.com/login
Navigate to the login page
```

Possible Playwright action:

```text
page.goto(...)
```

### Text Input

```text
Enter "john@test.com" in the username field
Type "john@test.com" into Username
Fill the email field with "john@test.com"
```

The agent should identify the correct page element using Playwright's available browser/page information.

### Click

```text
Click Login
Click the Login button
Press the Submit button
Select Login
```

The agent should identify the appropriate element using robust Playwright locators.

### Verification

```text
Verify that Dashboard is displayed
Verify that login was successful
Check that the welcome message is visible
Verify the page contains "Order Confirmed"
```

The agent should perform an appropriate Playwright assertion/check.

### Dropdown

```text
Select India from the Country dropdown
Choose "India" from Country
```

### Checkbox

```text
Select the Terms and Conditions checkbox
Uncheck Remember Me
```

### Radio Button

```text
Select Male
Select Credit Card
```

### Keyboard

```text
Press Enter
Press Escape
Press Tab
```

### Wait

```text
Wait until the Dashboard is visible
Wait for the Login button
```

The AI should prefer Playwright's built-in waiting mechanisms rather than unnecessary fixed delays.

---

# 6. AI Agent Architecture

Create an **AI Test Execution Agent**.

The agent should operate as follows:

```text
Plain English Test Step
        ↓
AI Understanding
        ↓
Intent Detection
        ↓
Browser/Page Inspection
        ↓
Locator Identification
        ↓
Playwright Action
        ↓
Result Validation
        ↓
Screenshot
        ↓
Next Step
```

The agent must execute the steps sequentially.

---

# 7. AI Agent Must Use Playwright

The backend must use **Playwright** as the browser automation engine.

Recommended implementation:

```text
Python Backend
      ↓
AI Agent
      ↓
Playwright Service
      ↓
Browser
```

The browser must run in:

```text
HEADLESS = FALSE
```

or the equivalent Playwright headed configuration.

The user must be able to see the actual browser window performing the actions.

---

# 8. Headed Execution

This is a mandatory requirement.

When the user clicks:

**Test Execute**

the backend should launch a real Playwright browser in headed mode.

Example conceptual flow:

```text
User clicks Test Execute
          ↓
Backend starts execution
          ↓
Playwright launches browser
          ↓
Browser window becomes visible
          ↓
AI Agent starts executing steps
          ↓
User watches browser actions
```

The system must not execute the primary test flow only in headless mode.

If the application is running on a remote server where the browser cannot physically appear on the user's desktop, the implementation must provide an appropriate browser-viewing mechanism, such as a remotely accessible browser display/VNC-style session.

Do not falsely claim that a server-side headed browser is visible on the user's local monitor without a remote-display mechanism.

---

# 9. Browser Interaction Strategy

The AI Agent should inspect the current page before selecting a locator whenever possible.

Locator preference:

1. Role-based locator
2. Accessible name
3. Label
4. Placeholder
5. Test ID / stable attribute
6. Text
7. CSS selector
8. XPath only when necessary

The AI Agent should avoid brittle selectors whenever reliable semantic information is available.

Example:

Instead of unnecessarily generating:

```text
#app > div:nth-child(2) > div > button
```

prefer an appropriate semantic locator such as:

```text
getByRole("button", { name: "Login" })
```

The actual locator must be generated based on the live page and available elements, not fabricated.

---

# 10. Locator Resolution

For every action, the AI Agent should attempt to identify the target element.

Example input:

```text
Click Login
```

Agent reasoning should result in an execution plan similar to:

```text
Intent:
CLICK

Target:
Login button

Locator strategy:
Role = button
Name = Login
```

Then execute through Playwright.

If multiple elements match, the agent should inspect the page and resolve the ambiguity.

If the target cannot be identified confidently, the step should fail with a clear reason.

Do NOT randomly click an element.

---

# 11. Handling Ambiguous Instructions

If the user writes:

```text
Click the button
```

and several buttons exist, the agent should not guess.

The result should be:

```text
FAILED

Reason:
The instruction "Click the button" is ambiguous because multiple
matching buttons were found on the current page.
```

Similarly:

```text
Enter John
```

without identifying a field should not result in a random input.

Report:

```text
FAILED

Reason:
Unable to determine which input field should contain "John".
```

---

# 12. AI Must Not Invent Information

Strict rules:

1. Do not invent URLs.
2. Do not invent credentials.
3. Do not invent test steps.
4. Do not invent expected results.
5. Do not invent selectors when the page does not provide enough evidence.
6. Do not invent test data.
7. Do not claim successful execution without evidence.
8. Do not mark a step as passed when Playwright failed.
9. Do not hide browser errors.
10. Do not silently skip failed steps.

If the required information cannot be determined:

```text
Insufficient information to execute.
```

If the problem is caused by the live webpage:

```text
Unable to identify the requested element on the current page.
```

---

# 13. Step-by-Step Execution

Every instruction in the text file should become an execution step.

Example:

```text
Test Case: Login

1. Open https://example.com/login
2. Enter "admin@test.com" in the username field
3. Enter "Password123" in the password field
4. Click Login
5. Verify Dashboard is displayed
```

Execution:

```text
Step 1 → PASS
Step 2 → PASS
Step 3 → PASS
Step 4 → PASS
Step 5 → PASS

Test Case → PASSED
```

If Step 4 fails:

```text
Step 1 → PASS
Step 2 → PASS
Step 3 → PASS
Step 4 → FAILED
Step 5 → SKIPPED

Test Case → FAILED
```

---

# 14. Screenshot After Every Step

Capture a screenshot after every meaningful execution step.

Example:

```text
Execution ID:
EXEC-20260808-001

TC_LOGIN_001_step_01.png
TC_LOGIN_001_step_02.png
TC_LOGIN_001_step_03.png
TC_LOGIN_001_step_04.png
TC_LOGIN_001_step_05.png
```

For a failed step, capture the browser state immediately after the failure where possible.

Screenshot metadata:

- Execution ID
- Test Case ID
- Step number
- Step description
- Status
- Timestamp
- Screenshot filename

---

# 15. Screenshot Viewer

Create a page called:

**Screenshots**

Users should be able to see execution evidence directly in the application.

Display:

```text
Test Case: TC_LOGIN_001

Step 1
Open login page
Status: PASS
[ Screenshot ]

Step 2
Enter username
Status: PASS
[ Screenshot ]

Step 3
Enter password
Status: PASS
[ Screenshot ]

Step 4
Click Login
Status: PASS
[ Screenshot ]

Step 5
Verify Dashboard
Status: PASS
[ Screenshot ]
```

Features:

- Thumbnail
- Full-screen preview
- Step name
- Step status
- Timestamp
- Test Case ID
- Execution ID
- Download screenshot

---

# 16. Live Execution UI

While the browser is running, the application should display live status.

Example:

```text
Execution Running

Test Case:
TC_LOGIN_001

Current Step:
Step 3 of 5

Action:
Enter password in the password field

Status:
RUNNING

Progress:
████████████░░░░░ 60%
```

Update the UI in real time using:

- WebSocket
- Server-Sent Events
- Or another appropriate real-time mechanism

---

# 17. Execution Console

Provide an execution log panel.

Example:

```text
[10:32:01] Execution started
[10:32:02] Browser launched in headed mode
[10:32:04] Test Case TC_LOGIN_001 started
[10:32:05] Step 1 started: Open login page
[10:32:06] Step 1 passed
[10:32:07] Screenshot captured
[10:32:08] Step 2 started: Enter username
[10:32:09] Step 2 passed
...
```

Do not expose:

- Passwords
- API keys
- Authentication tokens
- Other sensitive secrets

---

# 18. Execution Result

After all steps complete:

```text
Test Case:
TC_LOGIN_001

Total Steps: 5
Passed: 5
Failed: 0
Skipped: 0

Status:
PASSED
```

If any mandatory step fails:

```text
Status:
FAILED
```

A test must not be marked passed if its required verification failed.

---

# 19. Execution Completion Popup

After execution completes, display:

> **Test case execution completed**

Include:

- Total test cases
- Passed
- Failed
- Duration

Buttons:

- View Report
- View Screenshots
- Dashboard
- Close

For an infrastructure failure, show a different message such as:

> **Test execution could not be completed**

and provide the actual failure reason.

---

# 20. Execution History

Create:

**Execution History**

Display:

| Execution ID | File | Date | Total | Passed | Failed | Duration | Status |
|---|---|---|---:|---:|---:|---:|---|

Allow users to open an execution and see:

- Test cases
- Steps
- Status
- Screenshots
- Errors
- Execution logs
- Generated Playwright actions/code if retained

---

# 21. Test Case Format

The application should support simple Markdown and text syntax.

### Recommended format

```markdown
# Test Case: Login with valid credentials

## Steps

1. Open https://example.com/login
2. Enter "admin@test.com" in the username field
3. Enter "Password123" in the password field
4. Click the Login button
5. Verify that the Dashboard page is displayed
```

Multiple test cases may exist in one file.

Example:

```markdown
# Test Case: Valid Login

1. Open https://example.com/login
2. Enter "admin@test.com" in the username field
3. Enter "Password123" in the password field
4. Click Login
5. Verify Dashboard is displayed

# Test Case: Invalid Login

1. Open https://example.com/login
2. Enter "wrong@test.com" in the username field
3. Enter "WrongPassword" in the password field
4. Click Login
5. Verify that an invalid credentials message is displayed
```

The parser should identify each `Test Case` section automatically.

---

# 22. Optional Metadata

The user may optionally provide:

```markdown
# Test Case: Login

Module: Authentication
Priority: High
Environment: QA
Browser: Chromium

## Steps

1. Open https://example.com/login
2. Enter "admin@test.com" in the username field
3. Enter "Password123" in the password field
4. Click Login
5. Verify Dashboard is displayed
```

The system must continue to work if optional metadata is not provided.

---

# 23. Groq API Configuration

The application must provide a configuration page:

**AI Configuration**

Fields:

- Groq API Key
- Connection Status
- Test Connection
- Save
- Remove

The API key must be securely stored.

Never:

- Display the complete key
- Log the key
- Store it in frontend source code
- Commit it to Git
- Return it through an API response

Example status:

```text
Groq API
Connected
```

or:

```text
Groq API
Not Configured
```

---

# 24. AI Model Responsibilities

Groq is used for the AI reasoning layer.

The AI should:

1. Read the plain-English test.
2. Identify the test case.
3. Split instructions into steps.
4. Determine each step's intent.
5. Inspect available browser information.
6. Determine an appropriate Playwright action.
7. Execute the action.
8. Verify the result where requested.
9. Return structured execution information.

The AI must not simply generate a large Playwright script and assume it worked.

Execution must be based on actual Playwright browser results.

---

# 25. Preferred Agent Execution Model

Use an agent loop similar to:

```text
READ STEP
   ↓
UNDERSTAND STEP
   ↓
INSPECT PAGE
   ↓
SELECT ACTION
   ↓
EXECUTE PLAYWRIGHT ACTION
   ↓
OBSERVE RESULT
   ↓
CAPTURE SCREENSHOT
   ↓
RECORD RESULT
   ↓
NEXT STEP
```

This is preferred over blindly generating one large script and executing it without observing intermediate browser state.

---

# 26. Playwright Backend Service

Create a dedicated Playwright execution service.

Responsibilities:

- Browser lifecycle
- Context lifecycle
- Page lifecycle
- Navigation
- Locator discovery
- Actions
- Assertions
- Screenshot capture
- Error handling
- Browser cleanup

Use a supported browser such as Chromium by default.

Make browser selection configurable where practical.

---

# 27. Browser Session

For each execution:

```text
Create Execution
      ↓
Launch Browser
      ↓
Create Context
      ↓
Create Page
      ↓
Execute Test Cases
      ↓
Capture Evidence
      ↓
Close Page
      ↓
Close Context
      ↓
Close Browser
      ↓
Persist Final Result
```

If multiple test cases are executed, maintain clear isolation between test cases unless the user explicitly requests shared state.

---

# 28. Security

Implement:

- Secure authentication
- Password hashing
- Protected APIs
- Secure session/token handling
- Groq key encryption
- File validation
- File size limits
- Safe temporary-file handling
- Secure screenshot storage
- User-level authorization

A user must only be able to access their own:

- Test files
- Test cases
- Executions
- Screenshots
- Logs
- API configuration

---

# 29. Error Handling

Handle:

### File Errors

- Empty file
- Unsupported extension
- Invalid Markdown
- Invalid text structure
- No test steps found

### AI Errors

- Groq key missing
- Invalid API key
- Rate limit
- AI timeout
- Invalid AI response
- Unable to understand instruction

### Browser Errors

- Browser launch failure
- Navigation failure
- Timeout
- Element not found
- Multiple matching elements
- Page closed unexpectedly

### Execution Errors

- Step failure
- Assertion failure
- Screenshot failure
- Backend failure
- Unexpected browser state

Every error must be visible in the execution report.

---

# 30. Status Model

## Test Case Status

```text
NOT_EXECUTED
QUEUED
RUNNING
PASSED
FAILED
BLOCKED
ERROR
```

## Step Status

```text
PENDING
RUNNING
PASSED
FAILED
SKIPPED
ERROR
```

---

# 31. Dashboard Module-Wise Reporting

If the uploaded file contains:

```text
Module: Login
```

the dashboard should group results by module.

If no module is provided, group by test-case file or another clearly labeled default grouping.

Never invent module names.

Example:

```text
Login
---------
Total: 10
Passed: 8
Failed: 2

Checkout
---------
Total: 15
Passed: 14
Failed: 1
```

---

# 32. Suggested Technology Stack

## Frontend

- React
- TypeScript
- Vite
- React Router
- Recharts or equivalent
- Responsive UI

## Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

## AI

- Groq API
- Configurable Groq model

## Browser Automation

- Playwright
- Playwright MCP where MCP is used as the agent/browser interaction interface

## Real-Time Communication

- WebSocket or Server-Sent Events

---

# 33. Recommended Project Structure

```text
testcase-executor-ai/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── database/
│   │   ├── models/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── playwright/
│   │   ├── parsers/
│   │   ├── screenshots/
│   │   └── reporting/
│   ├── tests/
│   └── requirements.txt
│
├── test-data/
│   └── sample_login_test.md
│
├── screenshots/
├── execution-artifacts/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

# P — Purpose

The purpose of **Testcase Executor.AI** is to make automated browser testing accessible to QA engineers who may not want to write automation code.

The user experience should be:

```text
Write simple English
       ↓
Save as .txt or .md
       ↓
Upload
       ↓
Click Test Execute
       ↓
AI understands the instructions
       ↓
Playwright executes them
       ↓
Watch browser in headed mode
       ↓
Review screenshots
       ↓
Review results
```

The application should hide automation complexity from the user while maintaining complete execution evidence and traceability.

---

# O — Output Type

Build the application as a complete full-stack solution.

The implementation should include:

1. User registration.
2. User login.
3. Dashboard.
4. `.txt` upload.
5. `.md` upload.
6. Plain-English test-case parser.
7. AI Test Execution Agent.
8. Groq integration.
9. Playwright backend execution.
10. Headed browser execution.
11. Live execution status.
12. Step-level screenshots.
13. Screenshot viewer.
14. Execution history.
15. Execution details.
16. Pass/fail reporting.
17. Dashboard graphs.
18. Secure API-key configuration.
19. Error handling.
20. Database persistence.
21. Automated tests.
22. README documentation.
23. Environment configuration.
24. Sample `.txt` test case.
25. Sample `.md` test case.

---

# T — Technical and Quality Constraints

## 1. Primary Requirement

The application must accept **ONLY**:

```text
.txt
.md
```

for user-authored test cases.

Do not make Excel/CSV/JSON a prerequisite.

---

## 2. Natural Language Requirement

The user should be able to write instructions in ordinary English.

Example:

```text
Open the website.

Click Login.

Enter "admin@test.com" in the username field.

Enter "Password123" in the password field.

Click Sign In.

Verify that the Dashboard is visible.
```

The AI Agent must convert these instructions into browser actions.

---

## 3. Evidence Requirement

Every executed step must have evidence whenever technically possible.

Evidence includes:

- Step result
- Screenshot
- Timestamp
- Browser action
- Error details if failed

---

## 4. No False Results

The system must never report:

```text
PASSED
```

unless the Playwright execution actually succeeded.

Similarly, if an expected verification fails:

```text
FAILED
```

must be reported.

---

# 5. Acceptance Criteria

## Registration

- User can create an account.
- Duplicate accounts are rejected.
- Password is securely hashed.

## Login

- Registered user can log in.
- Invalid credentials are rejected.
- Dashboard is protected.

## File Upload

- `.txt` is accepted.
- `.md` is accepted.
- Unsupported files are rejected.
- Plain-English instructions are parsed.
- Multiple test cases can be detected.

## AI Execution

- Groq API key can be configured.
- AI understands simple English instructions.
- AI determines appropriate Playwright actions.
- AI does not invent missing information.
- Playwright performs the actual browser actions.

## Headed Mode

- Browser launches in headed mode.
- User can observe browser execution.
- Execution progress is visible in the application.

## Screenshots

- Screenshot captured after each meaningful step.
- Screenshots are associated with the correct test case and step.
- Screenshots can be viewed in the application.

## Reporting

- Pass/fail results are stored.
- Execution history is available.
- Dashboard statistics update automatically.
- Graphs use real execution data.

## Completion

After successful execution:

```text
Test case execution completed
```

is displayed.

The user can navigate to:

- Execution Report
- Screenshots
- Dashboard

---

# Final Product Vision

**Testcase Executor.AI** should provide a simple QA experience:

```text
                USER
                  │
                  ▼
       Write Plain English Steps
                  │
                  ▼
            .TXT / .MD
                  │
                  ▼
              UPLOAD
                  │
                  ▼
          AI TEST AGENT
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
 Understand Steps       Inspect Browser
       │                     │
       └──────────┬──────────┘
                  ▼
             PLAYWRIGHT
                  │
                  ▼
          HEADED BROWSER
                  │
                  ▼
          Execute Step 1
                  │
             Screenshot
                  │
                  ▼
          Execute Step 2
                  │
             Screenshot
                  │
                  ▼
             Continue
                  │
                  ▼
           FINAL RESULT
             /       \
          PASSED    FAILED
             \       /
              ▼     ▼
             REPORT
                │
                ▼
             DASHBOARD
```

The most important principle is:

> **The user writes the test in simple English. The AI Agent handles the automation. Playwright performs the real browser execution. The user can watch the headed browser and review screenshot evidence for every step.**
