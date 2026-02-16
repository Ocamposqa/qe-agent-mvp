import asyncio
import os
from browser_tools import BrowserManager
from security_auditor import SecurityAuditor
from reporting import TestReporter

async def test_active_scan():
    print("Starting Active Scan Test...")
    browser = BrowserManager(headless=True)
    auditor = SecurityAuditor()
    reporter = TestReporter("test_active_report.pdf")
    
    try:
        await browser.start()
        print("Browser started.")
        
        # Use absolute path or localhost if server is running. Assuming server is running on 8000.
        url = "http://localhost:8000/vulnerable_app.html"
        print(f"Navigating to {url}...")
        await browser.navigate(url)
        
        # Run Active Scan
        print("Running Active Scan...")
        await auditor.active_scan(browser)
        
        findings = auditor.get_findings()
        print(f"Security Findings: {len(findings)}")
        for f in findings:
            print(f"- [{f['severity']}] {f['type']}: {f['details']}")
            
        reporter.add_security_findings(findings)
        reporter.generate_report()
        print(f"Report generated: {reporter.filename}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_active_scan())
