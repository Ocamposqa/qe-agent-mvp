import os
import asyncio
import argparse
from dotenv import load_dotenv
from agent_logic import QEAgent
from browser_tools import BrowserManager
from reporting import TestReporter
from security_auditor import SecurityAuditor

# Load environment variables
load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Autonomous QE Agent (V2)")
    parser.add_argument("--url", type=str, help="Target URL to test", default=None)
    parser.add_argument("--instructions", type=str, help="Specific test instructions", default=None)
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is missing in .env file.")
        return

    print("Initializing Autonomous QE Agent (V2)...")
    
    # Initialize Components
    # Pass headless argument to BrowserManager
    browser_manager = BrowserManager(headless=args.headless)
    reporter = TestReporter("qe_agent_report.pdf")
    auditor = SecurityAuditor() # Initialize SecurityAuditor
    
    # Initialize Agent with Reporter
    agent = QEAgent(browser_manager, reporter)

    print("Agent Ready. Capabilities: Visual Navigation, Reporting, Human-in-the-loop.")
    
    # Determine Instructions
    if args.instructions:
        test_instruction = args.instructions
    elif args.url:
        # Generic instruction if only URL is provided
        test_instruction = f"""
        1. Navigate to '{args.url}'
        2. Analyze the page.
        3. Identify main interactive elements.
        4. Report any obvious visual bugs.
        """
    else:
        # Default Login Scenario
        test_instruction = """
        1. Navigate to 'https://the-internet.herokuapp.com/login'
        2. Analyze the page.
        3. Type 'tomsmith' into the #username field.
        4. Type 'SuperSecretPassword!' into the #password field.
        5. Click the Login button.
        6. Verify success.
        """

    print(f"Executing Test Scenario:\n{test_instruction}")
    
    try:
        await browser_manager.start()
        result = await agent.run(test_instruction)
        print("\n--- Test Execution Result ---")
        print(result)
        reporter.add_step(f"Execution Complete. Agent Output: {result}", "SUCCESS")
    except Exception as e:
        print(f"\nError during execution: {e}")
        reporter.add_step(f"Execution Error: {e}", "FAIL")
    finally:
        # 1. Capture Browser Logs
        logs = await browser_manager.get_logs()
        reporter.add_browser_logs(logs)

        # 2. Run Security Audit (Passive Phase)
        print("\nRunning Security Audit (Passive Scan)...")
        visited_responses = await browser_manager.get_responses()
        current_cookies = await browser_manager.get_cookies()
        
        # Analyze headers for unique URLs visited
        analyzed_urls = set()
        for response in visited_responses:
            url = response['url']
            if url not in analyzed_urls and response['status'] == 200:
                auditor.scan_headers(url, response['headers'])
                analyzed_urls.add(url)
                
        # Analyze cookies
        auditor.scan_cookies(current_cookies)
        
        # 3. Cleanup and Report
        print(f"Security Findings: {len(findings)} issues detected.")
        reporter.generate_report()
        print(f"Report generated: {reporter.filename}")
        
        await browser_manager.close()
        
        if os.path.exists("report_screenshots"):
            print(f"Screenshots captured: {len(os.listdir('report_screenshots'))}")
        else:
            print("No screenshots captured (directory missing).")

if __name__ == "__main__":
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    asyncio.run(main())
