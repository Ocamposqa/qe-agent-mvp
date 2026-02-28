# Quantum QE Enterprise 🚀

Quantum QE is an advanced, autonomous Multi-Agent Quality Engineering (QE) platform designed to orchestrate complex end-to-end testing, security audits, and functional validation against modern web applications. 

Designed under the **ISO/IEC 25010** software quality standard, Quantum QE leverages the power of Large Language Models (LLMs) and containerized Agentic execution to deliver deep analysis, actionable telemetry, and secure reporting.

## 🛠 Tech Stack

### Core Architecture (Agentic AI)
* **LangChain & LangGraph:** Powers the ReAct loop, tool orchestration, and multi-agent cyclic routing.
* **Azure OpenAI:** Enterprise-grade LLM intelligence (GPT-4o) for reasoning, parsing DOM structures, and identifying vulnerabilities.
* **Playwright:** Headless (and headful) browser automation for deep DOM inspection and functional UI testing.

### Backend (Orchestration & Bridge)
* **Python 3.12+**
* **FastAPI & Uvicorn:** Asynchronous REST APIs and WebSocket entry points.
* **Azure Services Bridge:** 
  * **Azure Web PubSub:** Real-time event broadcasting to the frontend UI.
  * **Azure Service Bus:** Message queueing for test mission payloads.
  * **Azure Cosmos DB:** (Planned) Vector storage for Agent memory and historical insights.

### Frontend (Mission Control Pilot)
* **Next.js 14+ (React):** Server-side rendered administration portal.
* **Tailwind CSS & Framer Motion:** Cyberpunk/Glassmorphic aesthetics with fluid telemetry animations.
* **Lucide React:** Modern, lightweight iconography.

---

## ⚙️ Setup Guide

### 1. Prerequisites
* Python 3.12 or higher.
* Node.js v20 LTS.
* Active LLM API Keys (OpenAI or Azure OpenAI).
* Wait... (Azure Web PubSub connection string if running in Cloud mode).

### 2. Backend Initialization
```bash
# Clone the repository
git clone <repository_url>
cd qe-agent-mvp

# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
.\venv\Scripts\Activate.ps1    # On Windows

# Install Python requirements
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium --with-deps
```

### 3. Frontend Initialization
```bash
cd qe-agent-ui
npm install
```

### 4. Configuration (Environment Variables)
Create a `.env` file in the root directory based on `.env.example`:
```env
OPENAI_API_KEY="sk-proj-..."
# Set to 'mock' for local development without Azure cloud
WEBPUBSUB_CONNECTION_STRING="mock" 
```

---

## 🚀 Quick Start

To launch the entire Enterprise Suite locally (Frontend + Backend), simply use the provided PowerShell script:

```bash
.\start_enterprise.ps1
```

Once booted, open your browser and navigate to the Mission Control Pilot UI at:
**`http://localhost:3001`**

From there, you can enter any target URL, provide custom directives, and hit **"ENGAGE AUTOPILOT"** to watch the agents execute the mission in real-time.

---
*Built with ❤️ by the Quantum Engineering Team*
