# QE Agent MVP

## Overview
This is an **Autonomous Quality Engineering (QE) Agent** designed to autonomously test web applications. It leverages **LangChain** and **LangGraph** for reasoning and decision-making, and **Playwright** for browser automation.

## Features
- **Autonomous Navigation**: Capability to navigate and interact with web pages.
- **Visual Analysis**: Uses browser tools to understand page context.
- **Reporting**: Generates PDF reports (`qe_agent_report.pdf`) and captures screenshots of test steps.
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
