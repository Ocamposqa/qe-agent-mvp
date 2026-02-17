import asyncio
import os
from browser_tools import BrowserManager
from security_auditor import SecurityAuditor
from reporting import TestReporter

async def test_passive_scan():
    print("Starting Passive Scan Test...")
    browser = BrowserManager(headless=True)
    auditor = SecurityAuditor()
    reporter = TestReporter("test_passive_report.pdf")
    
    try:
        await browser.start()
        print("Browser started.")
        
        url = "http://localhost:8000/vulnerable_app.html"
        print(f"Navigating to {url}...")
        await browser.navigate(url)
        
        # Simulate some interaction or just wait a bit
        await asyncio.sleep(2)
        
        print("Collecting data...")
        responses = await browser.get_responses()
        cookies = await browser.get_cookies()
        
        print(f"Captured {len(responses)} responses and {len(cookies)} cookies.")
        
        # Analyze
        analyzed_urls = set()
        for response in responses:
            r_url = response['url']
            if r_url not in analyzed_urls and response['status'] == 200:
                auditor.scan_headers(r_url, response['headers'])
                analyzed_urls.add(r_url)
        
        auditor.scan_cookies(cookies)
        
        findings = auditor.get_findings()
        print(f"Security Findings: {len(findings)}")
        for f in findings:
            print(f"- {f['type']}: {f['details']}")
            
        reporter.add_security_findings(findings)
        reporter.generate_report()
        print(f"Report generated: {reporter.filename}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_passive_scan())
