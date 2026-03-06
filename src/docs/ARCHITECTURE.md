# Quantum QE Enterprise Architecture

This document describes the flow of data, multi-agent reasoning, and cloud infrastructure bridging that powers Quantum QE.

## System Overview

Quantum QE is fundamentally an **Event-Driven, Multi-Agent System (MAS)** executed as a State Graph (powered by LangGraph). Instead of a rigid procedural script, the agents decide their own execution paths dynamically based on the state of the target DOM and the rules dictated by the Master Orchestrator.

## 1. The Core ReAct Loop

At the heart of our Multi-Agent framework is the **ReAct (Reason + Act)** loop. The execution follows these stages cyclically:

1. **Input / Mission Directive:** 
   * A mission is received via the APIM (Azure API Management) Gateway, providing a Target URL and custom testing instructions strings.
2. **Context Gathering (Observe):**
   * The `Navigator` Agent activates the Playwright browser context, navigates to the URL, and parses the visible DOM tree into a simplified accessibility representation.
3. **Reasoning (Think):**
   * The LLM evaluates the difference between the current DOM state, the user's objective, and any historical memory of the application structure. It reasons what tool is needed next.
4. **Execution (Act - Skills):**
   * The LLM triggers one of the pre-defined **Skills** (e.g., Click, Input Text, Extract Value, Analyze Form).
5. **State Update:**
   * The Browser applies the Skill. The new DOM tree is fed back into the orchestrator.
6. **Output / Handoff:**
   * Once the functional objective is achieved (or fails), control is routed to specialized sub-agents (e.g., the `Auditor` agent for security verification).

---

## 2. Multi-Agent Specialization

Instead of a single monolithic prompt, tasks are divided among specialized personas:

* **The Orchestrator:** The router node. It reads the user prompt and decides whether to send control to the Navigator, the Auditor, or the Reporter.
* **The Navigator (Functional QA):** Responsible strictly for interacting with UI elements, solving captchas, filling forms, and validating state changes (e.g., checking if a cart updated).
* **The Auditor (SecOps):** A non-interactive reasoning engine. It takes the final trace of the Navigator (Cookies, Headers, DOM structures) and performs a passive/active vulnerability check mapped to the OWASP Top 10.

---

## 3. Azure Cloud Bridge

Because executing browser contexts and streaming reasoning logs takes seconds or minutes, the backend architecture avoids holding standard REST HTTP connections open.

### The Flow:
1. **Frontend to Backend (Trigger):** The Next.js UI sends an `HTTP POST` payload to the FastAPI router.
2. **Asynchronous Hand-off (Service Bus):** If configured, FastAPI does not run the test. It enqueues the JSON payload into an Azure Service Bus Topic.
3. **Execution Workers (ACA):** Azure Container Apps (running headless Chromium via Playwright) consume messages off the bus, allowing infinite parallel scaling.
4. **Live Telemetry Stream (Web PubSub):** As the Agent navigates and reasons, it emits tiny JSON logs (`[AGENT] Clicking login_button...`). These logs are instantly pushed via **Azure Web PubSub** back to the listening Next.js UI using WebSockets.
5. **Memory Persistence (Cosmos DB):** At the end of the mission, the final report, token consumption delta, and security findings are committed to Azure Cosmos DB for reporting.
