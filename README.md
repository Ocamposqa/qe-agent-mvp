# QE Agent MVP

## Overview
This is an **Autonomous Quality Engineering (QE) Agent** designed to autonomously test web applications. It leverages **LangChain** and **LangGraph** for reasoning and decision-making, and **Playwright** for browser automation.

## Features
- **Autonomous Navigation**: Capability to navigate and interact with web pages using natural language instructions.
- **Robust Selectors**: Identifies elements using test attributes (`data-testid`, `data-cy`, `aria-label`) for improved reliability on modern web apps.
- **Visual Analysis**: Uses browser tools to understand page context and capture screenshots of every step.
- **Enhanced Reporting**: Generates PDF reports (`qe_agent_report.pdf`) that include:
    - Step-by-step screenshots.
    - Browser console logs and JS errors.
    - Network request failures.
- **Error Handling**: Gracefully handles navigation timeouts and errors without crashing, reporting them as failed steps.
- **Headless Mode**: Supports running tests in the background without a visible UI.
- **Command Line Interface (CLI)**: Flexible execution with custom URLs and instructions.
- **Human-in-the-Loop**: Can ask the user for help when stuck.

## Components
- **`main.py`**: Entry point for running test scenarios.
- **`agent_logic.py`**: Core agent logic using ReAct pattern.
- **`browser_tools.py`**: Playwright integration for browser interactions.
- **`reporting.py`**: PDF reporting and screenshot management.
- **`security_auditor.py`**: Security scanning logic (Passive & Active).

## Capabilities

### 1. Functional Testing
- **Autonomous Navigation**: Takes high-level natural language instructions (e.g., "Login and search for X") and executes them without pre-defined scripts.
- **Visual Analysis**: Uses a custom "Simplified DOM" and screenshots to understand page state and interactive elements.
- **Human-in-the-Loop**: Can pause execution to ask the user for help if stuck or confused by the UI.
- **Robust Interaction**: uses resilient selectors (`data-testid`, text content, accessibility roles) to click, type, and navigate despite DOM changes.

### 2. Security Auditing (AppSec)
- **Passive Scanning**:
    - **Security Headers**: Detects missing headers like `Content-Security-Policy`, `HSTS`, `X-Frame-Options`.
    - **Insecure Cookies**: Flags cookies missing `Secure`, `HttpOnly`, or `SameSite` attributes.
- **Active Scanning (Fuzzing)**:
    - **Input Discovery**: Automatically identifies input fields (`<input>`, `<textarea>`) on the page.
    - **Vulnerability Injection**: Injects payloads to test for Reflected XSS (`<script>...`) and SQL Injection.
    - **Reflection Analysis**: Inspects raw HTML responses to detect unescaped payload reflection.
- **Security Mindset**:
    - **Sensitive Data Detection**: Actively monitors page content for exposed API keys, secrets, or PII.
    - **IDOR Awareness**: Flags potential IDOR vectors in URLs (e.g., `/user/123`).

### 3. Reporting & Resilience
- **Comprehensive PDF Report**: Generates a single report containing:
    - Step-by-step execution log with screenshots.
    - Browser console logs and network errors.
    - **Security Insights**: A dedicated section listing all security findings with severity (Critical, High, Medium, Low) and remediation advice.
- **Self-Healing**: Handles navigation timeouts, unexpected popups, and shutdowns gracefully without crashing the entire suite.

## Setup
1.  Install dependencies: `pip install -r requirements.txt`
2.  Set up environment variables (e.g., `OPENAI_API_KEY`) in `.env`.
3.  Run the agent: `python main.py`

## Usage (CLI)

You can run the agent with various options:

**1. Default Login Test:**
   ```bash
   python main.py
   ```

**2. Test a Custom URL:**
   ```bash
   # Generates generic testing instructions for the page
   python main.py --url https://example.com
   ```

**3. Run Headless (No UI):**
   ```bash
   python main.py --headless
   ```

**4. Custom Instructions:**
   ```bash
   python main.py --instructions "1. Go to google.com 2. Search for 'Playwright'"
   ```
