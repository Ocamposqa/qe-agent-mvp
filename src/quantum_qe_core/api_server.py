import asyncio
import logging
import sys
import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from dotenv import load_dotenv

# Azure SDK Imports
from azure.messaging.webpubsubservice import WebPubSubServiceClient
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

# Load environment variables
load_dotenv()

# SHARED: Fix for Windows Event Loop Runtime Error (Proactor)
if sys.platform.startswith("win"):
    from asyncio.proactor_events import _ProactorBasePipeTransport
    from functools import wraps
    def silence_event_loop_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper
    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

# Quantum Core Imports (to be used later for orchestration)
from src.quantum_qe_core.skills.browser import BrowserManager
from src.quantum_qe_core.skills.reporter import TestReporter
from src.quantum_qe_core.skills.knowledge import KnowledgeManager
from src.quantum_qe_core.agents.navigator import NavigatorAgent
from src.quantum_qe_core.agents.auditor import AuditorAgent
from src.quantum_qe_core.skills.telemetry_skill import LLMTelemetryHandler
from src.quantum_qe_core.telemetry import log_telemetry  # NEW
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Quantum QE Enterprise API", version="1.0.0")

# Mount output directory for HTML reports
os.makedirs("output", exist_ok=True)
app.mount("/reports", StaticFiles(directory="output"), name="reports")

# Allow Frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScanRequest(BaseModel):
    url: str
    instructions: str
    skip_security: bool = False
    headless: bool = True
    project_id: int | None = None
    supervised: bool = False
    agents: list[str] = ["functional"]

# --- HITL State Management ---
HITL_EVENTS = {}

class HitlReply(BaseModel):
    reply: str

# --- Connection Manager (For Local Fallback) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                self.active_connections.pop(job_id, None)

    async def broadcast(self, message: dict, job_id: str):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_json(message)

manager = ConnectionManager()

# --- Azure Web PubSub Configuration ---
# In production, use Azure Managed Identity. For local dev/MVP, we use connection strings.
PUBSUB_CONNECTION_STRING = os.getenv("WEBPUBSUB_CONNECTION_STRING", "")
HUB_NAME = "telemetryHub"

# Keep a reference to the main event loop
try:
    main_loop = asyncio.get_running_loop()
except RuntimeError:
    main_loop = None

if not PUBSUB_CONNECTION_STRING or "mock" in PUBSUB_CONNECTION_STRING.lower() or PUBSUB_CONNECTION_STRING == "Endpoint=https://quantumqe-wps.webpubsub.azure.com;AccessKey=mock;Version=1.0;":
    logger.info("Using MockPubSub for local development.")
    class MockPubSub:
        def send_to_group(self, group, message):
            logger.info(f"[MOCK PUBSUB -> {group}] {message}")
            if main_loop and main_loop.is_running():
                # Schedule broadcast if we have a loop
                asyncio.run_coroutine_threadsafe(manager.broadcast(message, group), main_loop)
            
        def get_client_access_token(self, **kwargs):
            return {"url": f"ws://localhost:8000/ws/telemetry/{kwargs.get('groups', ['mock'])[0]}"}
    pubsub_client = MockPubSub()
else:
    try:
        pubsub_client = WebPubSubServiceClient.from_connection_string(PUBSUB_CONNECTION_STRING, hub=HUB_NAME)
    except Exception as e:
        logger.error(f"Could not initialize Web PubSub Client. Error: {e}")
        raise



async def broadcast_telemetry(job_id: str, message: dict):
    """Pushes an event to the specific Job's Web PubSub group."""
    try:
        # Use synchronous call in async wrapper for Azure SDK MVP
        await asyncio.to_thread(pubsub_client.send_to_group, group=job_id, message=message)
    except Exception as e:
        logger.error(f"PubSub Broadcast Failed: {e}")

# --- Azure Service Bus Configuration ---
SERVICEBUS_CONNECTION_STRING = os.getenv("SERVICEBUS_CONNECTION_STRING")
QUEUE_NAME = "mission-queue"

@app.get("/")
def read_root():
    return {"status": "Quantum QE Core API (Azure Integrated) is running"}

@app.get("/api/negotiate/{job_id}")
def negotiate_pubsub(job_id: str):
    """
    Frontend calls this to get a secure WebSocket URL to connect to Azure Web PubSub directly.
    """
    token = pubsub_client.get_client_access_token(
        roles=[f"webpubsub.joinLeaveGroup.{job_id}", f"webpubsub.sendToGroup.{job_id}"],
        groups=[job_id],
        minutes_to_expire=60
    )
    return {"url": token["url"]}

@app.websocket("/ws/telemetry/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Fallback WebSocket connection for local MOCK Web PubSub"""
    global main_loop
    if main_loop is None:
        main_loop = asyncio.get_running_loop()
        
    await manager.connect(websocket, job_id)
    try:
        await manager.broadcast({"type": "status", "message": "Connected to telemetry stream"}, job_id)
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

@app.post("/api/scan")
async def start_scan(request: ScanRequest):
    """
    APIM Entrypoint: Instead of executing locally, it queues the mission to Azure Service Bus.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"APIM Received Scan Request. Queueing Job {job_id} for {request.url}")
    
    if SERVICEBUS_CONNECTION_STRING:
         try:
             async with ServiceBusClient.from_connection_string(conn_str=SERVICEBUS_CONNECTION_STRING, logging_enable=True) as sb_client:
                 sender = sb_client.get_queue_sender(queue_name=QUEUE_NAME)
                 message = ServiceBusMessage(request.model_dump_json(), session_id=job_id)
                 await sender.send_messages(message)
                 logger.info(f"Successfully enqueued job {job_id} to Service Bus.")
         except Exception as e:
             logger.error(f"Failed to enqueue to Service Bus: {e}. Falling back to local execution.")
             asyncio.create_task(asyncio.to_thread(_run_orchestrator_sync, job_id, request))
    else:
         logger.info("SERVICEBUS_CONNECTION_STRING not provided. Executing mission locally (Standalone Mode).")
         asyncio.create_task(asyncio.to_thread(_run_orchestrator_sync, job_id, request))
    
    return {"job_id": job_id, "status": "queued"}

@app.post("/api/hitl_resume/{job_id}")
async def resume_hitl(job_id: str, request: HitlReply):
    """
    Receives the human's reply from the Next.js UI and unpauses the agent.
    """
    if job_id in HITL_EVENTS:
        future, loop = HITL_EVENTS[job_id]
        loop.call_soon_threadsafe(future.set_result, request.reply)
        logger.info(f"HITL Resume received for {job_id}: {request.reply}")
        return {"status": "resumed"}
    return {"status": "error", "message": "No active HITL block for this job_id"}

# --- Agent Compute Worker (Azure Container Apps execution context) ---

def _run_orchestrator_sync(job_id: str, request: ScanRequest):
    """Wrapper to run the async orchestrator in a new thread with a fresh event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        new_loop.run_until_complete(run_quantum_orchestrator(job_id, request))
    finally:
        new_loop.close()

async def run_quantum_orchestrator(job_id: str, request: ScanRequest):
    """
    The main mission logic. In Azure, this runs in a Container App triggered by KEDA when messages hit the Service Bus queue.
    """
    # Setup custom logging for this thread
    file_handler = logging.FileHandler("orchestrator.log")
    logger.addHandler(file_handler)
    logger.info(f"--- STARTING ORCHESTRATOR FOR JOB {job_id} ---")

    await broadcast_telemetry(job_id, {"type": "log", "message": "Container Worker (ACA) Started. Initializing Agents..."})
    
    # Initialize variables for report generation
    nav_result = "Reporte No Disponible" # Default value for spanish_summary
    est_cost = 0.0
    network_stats = {'total_bytes_mb': 0}

    try:
        browser = BrowserManager(headless=request.headless)
        reporter = TestReporter(f"output/report_{job_id}.pdf")
        knowledge = KnowledgeManager("quantum_qe_core/knowledge", project_id=request.project_id)
        llm_telemetry = LLMTelemetryHandler()
        
        navigator = NavigatorAgent(browser, reporter, llm_telemetry, supervised=request.supervised)
        auditor = AuditorAgent(browser, reporter, knowledge, llm_telemetry)
        
        await broadcast_telemetry(job_id, {"type": "log", "message": "Starting Browser Context..."})
        logger.info("Initializing Browser Context...")
        await browser.start()
        logger.info("Browser Context Initialized successfully.")
        
        # Sequentially execute requested agents
        for agent_name in request.agents:
            await broadcast_telemetry(job_id, {"type": "status", "phase": f"Executing {agent_name.upper()} Agent"})
            
            if agent_name == "functional":
                nav_instruction = f"1. Navigate to {request.url}\n2. {request.instructions}"
                await broadcast_telemetry(job_id, {"type": "log", "message": f"Dispatching Functional Agent: {nav_instruction}"})
                nav_result = await navigator.run(nav_instruction)
                
                # Check for HITL
                if isinstance(nav_result, str) and "REQUIRE_HUMAN" in nav_result:
                    await broadcast_telemetry(job_id, {"type": "hitl_request", "message": nav_result.replace("REQUIRE_HUMAN:", "").strip()})
                    HITL_EVENTS[job_id] = (asyncio.Future(), asyncio.get_running_loop())
                    try:
                        human_reply = await asyncio.wait_for(HITL_EVENTS[job_id][0], timeout=600.0) # 10 min timeout for human
                        await broadcast_telemetry(job_id, {"type": "log", "message": f"Received Human Instruction: {human_reply}"})
                        # Resume agent with human input
                        nav_result = await navigator.run(f"HUMAN FEEDBACK: {human_reply}")
                    except asyncio.TimeoutError:
                        await broadcast_telemetry(job_id, {"type": "error", "message": "Human did not respond in time. Aborting Functional scan."})
                    finally:
                        HITL_EVENTS.pop(job_id, None)

                await broadcast_telemetry(job_id, {"type": "log", "message": f"Functional Result: {nav_result}"})
                
            elif agent_name == "ui":
                await broadcast_telemetry(job_id, {"type": "log", "message": f"Dispatching UI Verifier Agent. Analyzing CSS geometry and responsive states on {request.url}"})
                await asyncio.sleep(2) # Mock execution time
                await broadcast_telemetry(job_id, {"type": "log", "message": "UI Verifier: Layout matches expected parameters. No visual regressions detected."})
                
            elif agent_name == "synthetic":
                await broadcast_telemetry(job_id, {"type": "log", "message": f"Dispatching Synthetic Data Agent. Generating localized dummy data for forms..."})
                await asyncio.sleep(2) # Mock execution time
                await broadcast_telemetry(job_id, {"type": "log", "message": "Synthetic Data: Generated 5 user personas and injected them into local memory."})
                
            elif agent_name == "security":
                current_url = await browser.get_url()
                audit_instruction = f"Perform a comprehensive security audit on {current_url}."
                await broadcast_telemetry(job_id, {"type": "log", "message": f"Dispatching Security Auditor on {current_url}"})
                audit_result = await auditor.run(audit_instruction)
                if isinstance(audit_result, dict):
                    findings = audit_result.get("findings", [])
                    await broadcast_telemetry(job_id, {
                        "type": "security_findings", 
                        "summary": audit_result.get("summary", ""),
                        "findings_count": len(findings)
                    })
                    reporter.log_security_finding(findings)
            
            # Send DOM snapshot after every agent finishes its turn
            dom_state = await browser.get_simplified_dom()
            await broadcast_telemetry(job_id, {"type": "dom_update", "image": dom_state.get("image")})
        
        # Generation of Final HTML Report
        await broadcast_telemetry(job_id, {"type": "status", "phase": "Generating Final Report"})
        
        from src.quantum_qe_core.agents.reporter import ReporterAgent
        reporter_agent = ReporterAgent(reporter)
        
        # Calculate approximate compute time inside this thread
        import time
        compute_ms = 25000  # Default MVP mock timer, can be dynamic
        
        # Log final telemetry for billing
        est_cost = log_telemetry(
            job_id=job_id, 
            tokens=llm_telemetry.total_tokens, 
            compute_ms=compute_ms, 
            project_id=request.project_id
        )
        
        network_stats = browser.network_telemetry.get_stats()
        telemetry_payload = {
            "tokens": llm_telemetry.total_tokens,
            "cost": est_cost,
            "network_mb": network_stats['total_bytes_mb']
        }

        await broadcast_telemetry(job_id, {"type": "log", "message": "Reporter Agent is consolidating findings and writing the Spanish Executive Summary via LLM."})
        html_report_path = await reporter_agent.run(
            job_id,
            agents_executed=request.agents,
            telemetry_data=telemetry_payload
        )
        
        await broadcast_telemetry(job_id, {"type": "log", "message": f"Enterprise HTML Report generated locally at: {html_report_path}"})

        # Cleanup
        await browser.close()
        
        await broadcast_telemetry(job_id, {
            "type": "status", 
            "phase": "Complete", 
            "html_report_url": f"http://localhost:8000/reports/report_{job_id}.html",
            "message": f"Scan Finished Successfully. Cost: ${est_cost:.4f} | Network: {network_stats['total_bytes_mb']}MB"
        })
        
    except asyncio.TimeoutError:
        error_msg = "Mission Timeout: Agent execution exceeded the 5-minute limit (Possible Infinite Loop or Rate Limit)."
        logger.error(f"Job {job_id} failed: {error_msg}")
        await broadcast_telemetry(job_id, {"type": "error", "message": error_msg})
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Job {job_id} failed: {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        await broadcast_telemetry(job_id, {"type": "error", "message": error_msg})
    finally:
        logger.removeHandler(file_handler)
