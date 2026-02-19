import os
import asyncio
import argparse
from dotenv import load_dotenv

# Enterprise Core Imports
from quantum_qe_core.skills.browser import BrowserManager
from quantum_qe_core.skills.reporter import TestReporter
from quantum_qe_core.skills.knowledge import KnowledgeManager
from quantum_qe_core.agents.navigator import NavigatorAgent
from quantum_qe_core.agents.auditor import AuditorAgent

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

async def main():
    parser = argparse.ArgumentParser(description="Quantum QE Core (Enterprise Architecture)")
    parser.add_argument("--url", type=str, help="Target URL", default=None)
    parser.add_argument("--instructions", type=str, help="Functional Test Instructions", default="Login as admin/password and search for XSS payload.")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--skip-security", action="store_true", help="Skip the security audit phase")
    args = parser.parse_args()

    # Heuristic: Check if instructions imply skipping security
    if "no security" in args.instructions.lower() or "no hagas un check de seguridad" in args.instructions.lower():
        args.skip_security = True
        print("[INFO] detected 'no security' instruction. Skipping Security Phase.")

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is missing.")
        return

    print("Initializing Quantum QE Core (Multi-Agent System + RAG)...")
    
    # Shared Resources (Skills)
    browser = BrowserManager(headless=args.headless)
    reporter = TestReporter("output/quantum_core_report.pdf")
    knowledge = KnowledgeManager("quantum_qe_core/knowledge")
    
    # Initialize Agents
    navigator = NavigatorAgent(browser, reporter)
    auditor = AuditorAgent(browser, reporter, knowledge)
    
    print("Agents Ready: Navigator (UI) & Auditor (AppSec + RAG).")
    
    try:
        await browser.start()
        
        # Phase 1: functional Testing (Navigator)
        print("\n--- Phase 1: Functional Testing (Navigator) ---")
        if args.url:
            nav_instruction = f"1. Navigate to {args.url}\n2. {args.instructions}"
        else:
            nav_instruction = args.instructions
            
        nav_result = await navigator.run(nav_instruction)
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
        except Exception as e:
             print(f"Report Generation Failed: {e}")
             
        await browser.close()
        print("Quantum Core Shutdown.")

if __name__ == "__main__":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    asyncio.run(main())
