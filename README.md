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
