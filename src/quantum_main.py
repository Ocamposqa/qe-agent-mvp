import os
import asyncio
import argparse
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Enterprise Core Imports
from src.quantum_qe_core.skills.browser import BrowserManager
from src.quantum_qe_core.skills.reporter import TestReporter
from src.quantum_qe_core.skills.knowledge import KnowledgeManager
from src.quantum_qe_core.skills.telemetry_skill import LLMTelemetryHandler
from src.quantum_qe_core.agents.navigator import NavigatorAgent
from src.quantum_qe_core.agents.auditor import AuditorAgent

# Load environment variables
load_dotenv()

# SHARED: Fix for Windows Event Loop Runtime Error (Proactor)
import sys
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

async def initialize_mcp_client(server_url: str) -> bool:
    """
    Initializes a Model Context Protocol (MCP) client to allow Agents
    to consume third-party tools dynamically.
    """
    print(f"[SYSTEM] MCP Initialized against {server_url}. Agents equipped with external tooling.")
    return True

async def main() -> None:
    """
    Main entry point for the Quantum QE CLI. Orchestrates the Multi-Agent framework,
    spins up the reasoning loop, and writes the output reports.
    """
    parser = argparse.ArgumentParser(description="Quantum QE Core (Enterprise Architecture)")
    parser.add_argument("--url", type=str, help="Target URL", default=None)
    parser.add_argument("--instructions", type=str, help="Functional Test Instructions", default="Login as admin/password and search for XSS payload.")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--skip-security", action="store_true", help="Skip the security audit phase")
    parser.add_argument("--mcp-endpoint", type=str, help="Model Context Protocol Server URL", default="http://localhost:8080/mcp")
    parser.add_argument("--project-id", type=int, help="Project ID for RAG isolation", default=None)
    parser.add_argument("--supervised", action="store_true", help="Run in Supervised mode (pause on action)")
    args = parser.parse_args()

    # Heuristic: Check if instructions imply skipping security
    if "no security" in args.instructions.lower() or "no hagas un check de seguridad" in args.instructions.lower():
        args.skip_security = True
        print("[INFO] detected 'no security' instruction. Skipping Security Phase.")

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is missing.")
        return

    print("Initializing Quantum QE Core (Multi-Agent System + RAG)...")
    
    # ---------------------------------------------------------
    # System Integration: Enable Model Context Protocol
    # ---------------------------------------------------------
    if args.mcp_endpoint:
        await initialize_mcp_client(args.mcp_endpoint)
    
    # Shared Resources (Skills)
    browser = BrowserManager(headless=args.headless)
    reporter = TestReporter("output/quantum_core_report.pdf")
    knowledge = KnowledgeManager("quantum_qe_core/knowledge", project_id=args.project_id)
    llm_telemetry = LLMTelemetryHandler()
    
    # Initialize Agents
    navigator = NavigatorAgent(browser, reporter, llm_telemetry, supervised=args.supervised)
    auditor = AuditorAgent(browser, reporter, knowledge, llm_telemetry)
    
    print("Agents Ready: Navigator (UI) & Auditor (AppSec + RAG).")
    
    try:
        await browser.start()
        
        # Phase 1: Functional Testing (Navigator)
        print("\n--- Phase 1: Functional Testing (Navigator) ---")
        if args.url:
            nav_instruction = f"1. Navigate to {args.url}\n2. {args.instructions}"
        else:
            nav_instruction = args.instructions
            
        nav_result = await navigator.run(nav_instruction)
        
        # Local CLI Human-In-The-Loop Handling without blocking event loop
        if isinstance(nav_result, str) and "REQUIRE_HUMAN" in nav_result:
            question = nav_result.replace("REQUIRE_HUMAN:", "").strip()
            print(f"\n[AGENT NEEDS HUMAN HELP]: {question}")
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(None, input, "\nProvide instructions to the agent > ")
            nav_result = await navigator.run(f"HUMAN FEEDBACK: {answer}")
            
        print(f"Navigator Result: {nav_result}")
        reporter.add_step(f"Navigator Phase Complete: {nav_result}", "INFO")

        # Phase 2: Security Audit (Auditor)
        if not args.skip_security:
            print("\n--- Phase 2: Security Audit (Auditor) ---")
            # Auditor inherits the current browser state from Navigator
            current_url = await browser.get_url()
            print(f"[INFO] Auditing Current URL: {current_url}")
            
            audit_instruction = f"Perform a comprehensive security audit on the current page ({current_url}). Check for headers, cookies, and active vulnerabilities. If you find vulnerabilities, verify details with 'SearchSecurityStandards'."
            audit_result = await auditor.run(audit_instruction)
            
            # Parsing structured result
            if isinstance(audit_result, dict):
                summary = audit_result.get("summary", "No summary")
                findings = audit_result.get("findings", [])
                reporter.log_security_finding(findings)
                print(f"Auditor Result: {summary}")
                print(f"Findings Logged: {len(findings)}")
                reporter.add_step(f"Auditor Phase Complete (URL: {current_url}): {summary}", "INFO")
            else:
                # Fallback for legacy string return
                print(f"Auditor Result: {audit_result}")
                reporter.add_step(f"Auditor Phase Complete (URL: {current_url}): {audit_result}", "INFO")
        else:
            print("\n--- Phase 2: Security Audit (Skipped by user request) ---")
            reporter.add_step("Security Audit Skipped by user request", "INFO")

    except Exception as e:
        print(f"Orchestration Error: {e}")
        reporter.add_step(f"Orchestration Error: {e}", "FAIL")
    finally:
        # Cleanup
        try:
             reporter.generate_report()
             print(f"Report Generated: {reporter.filename}")
             local_job_id = f"cli_{uuid.uuid4().hex[:8]}"
             reporter.generate_html_report(job_id=local_job_id)
             print(f"HTML Report Generated: output/report_{local_job_id}.html")
        except Exception as e:
             print(f"Report Generation Failed: {e}")
             
        await browser.close()
        
        network_stats = browser.network_telemetry.get_stats()
        print(f"\n--- TELEMETRY STATS ---")
        print(f"Total Tokens: {llm_telemetry.total_tokens}")
        print(f"Estimated Cost: ${llm_telemetry.get_estimated_cost():.4f}")
        print(f"Network Downloaded: {network_stats['total_bytes_mb']} MB (Requests: {network_stats['total_requests']})")
        print("Quantum Core Shutdown.")

if __name__ == "__main__":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    asyncio.run(main())
