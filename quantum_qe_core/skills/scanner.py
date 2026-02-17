import asyncio
from typing import List, Dict, Any
from langchain_core.tools import Tool

class SecurityAuditor:
    def __init__(self):
        self.findings = []

    def scan_headers(self, url: str, headers: Dict[str, str]):
        """Analyzes HTTP response headers for missing security mechanisms."""
        required_headers = {
            "Content-Security-Policy": "Mitigates XSS and data injection attacks.",
            "Strict-Transport-Security": "Enforces HTTPS connections (HSTS).",
            "X-Frame-Options": "Prevents Clickjacking attacks.",
            "X-Content-Type-Options": "Prevents MIME sniffing (nosniff).",
            "Referrer-Policy": "Controls how much referrer information is included with requests."
        }

        # Normalize headers to lowercase for case-insensitive comparison
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for header, description in required_headers.items():
            if header.lower() not in headers_lower:
                self.findings.append({
                    "severity": "Medium",
                    "type": "Missing Header",
                    "details": f"Missing {header} on {url}",
                    "remediation": f"Implement {header}. {description}"
                })

    def scan_cookies(self, cookies: List[Dict[str, Any]]):
        """Analyzes cookies for missing security flags."""
        for cookie in cookies:
            name = cookie.get('name', 'Unknown')
            
            if not cookie.get('secure', False):
                self.findings.append({
                    "severity": "Low",
                    "type": "Insecure Cookie",
                    "details": f"Cookie '{name}' is missing the 'Secure' flag.",
                    "remediation": "Set the 'Secure' flag to ensure the cookie is only sent over HTTPS."
                })
            
            if not cookie.get('httpOnly', False):
                self.findings.append({
                    "severity": "Medium",
                    "type": "Insecure Cookie",
                    "details": f"Cookie '{name}' is missing the 'HttpOnly' flag.",
                    "remediation": "Set the 'HttpOnly' flag to prevent access via JavaScript (XSS protection)."
                })
            
            same_site = cookie.get('sameSite', 'None')
            if same_site == 'None' or not same_site:
                self.findings.append({
                    "severity": "Low",
                    "type": "Insecure Cookie",
                    "details": f"Cookie '{name}' has weak 'SameSite' policy ({same_site}).",
                    "remediation": "Set 'SameSite' to 'Lax' or 'Strict' to mitigate CSRF."
                })

    async def active_scan(self, browser_manager):
        """Performs active scanning (fuzzing) on identified inputs."""
        inputs = await browser_manager.get_input_elements()
        if not inputs:
            return

        print(f"Starting Active Scan on {len(inputs)} inputs...")

        for input_elem in inputs:
            selector = input_elem['selector']
            print(f"Fuzzing input: {selector}")

            # 1. Reflected XSS Test
            xss_payload = "<script>console.log('XSS_TEST')</script>"
            await browser_manager.type_text(selector, xss_payload)
            # Try to trigger it (press Enter)
            await browser_manager.press_key(selector, "Enter")
            
            # Allow time for processing
            await asyncio.sleep(1)
            
            # Check for reflection (Basic)
            # Use get_content to see raw HTML (including scripts that get_simplified_dom might remove)
            page_content = await browser_manager.get_content()
            
            # If the payload appears unescaped in the HTML, it's a likely vulnerability.
            if xss_payload in page_content:
                 self.findings.append({
                    "severity": "High",
                    "type": "Reflected Input (Potential XSS)",
                    "details": f"Input at {selector} reflects injected values without escaping: {xss_payload}",
                    "remediation": "Ensure all user input is output encoded."
                })

            # 2. SQL Injection Test (Basic)
            sqli_payload = "' OR '1'='1"
            await browser_manager.type_text(selector, sqli_payload)
            await browser_manager.press_key(selector, "Enter")
            await asyncio.sleep(1)
            
            # Re-fetch content for SQLi check
            page_content_sqli = await browser_manager.get_content()
            
            sql_errors = ["syntax error", "mysql", "sql syntax", "unrecognized token"]
            for err in sql_errors:
                if err in page_content_sqli.lower():
                    self.findings.append({
                        "severity": "Critical",
                        "type": "SQL Injection Susceptibility",
                        "details": f"Input at {selector} caused a potential database error: '{err}'",
                        "remediation": "Use parameterized queries to prevent SQL injection."
                    })

    def get_findings(self) -> List[Dict[str, Any]]:
        return self.findings

    def get_tools(self, browser_manager):
        """Returns tools for security scanning."""
        
        async def active_scan_wrapper(input_str: str = ""):
            """Triggers active scan on current page. Input is ignored."""
            print(f"[DEBUG] Active Scan triggered via Tool")
            await self.active_scan(browser_manager)
            return f"Active Scan Complete. Total findings: {len(self.findings)}"

        async def passive_scan_wrapper(url: str):
            """Triggers passive scan for a specific URL."""
            print(f"[DEBUG] Passive Scan triggered for {url}")
            responses = await browser_manager.get_responses()
            cookies = await browser_manager.get_cookies()
            
            # Scan headers
            scanned = False
            for response in responses:
                # Simple matching
                if url in response['url']: 
                    self.scan_headers(response['url'], response['headers'])
                    scanned = True
            
            # Scan cookies
            self.scan_cookies(cookies)
            
            if not scanned:
                return f"Passive Scan: No captured response found for {url}. Parsed cookies only."
            return f"Passive Scan Complete. Total findings: {len(self.findings)}"

        return [
            Tool(
                name="SecurityActiveScan",
                func=active_scan_wrapper,
                coroutine=active_scan_wrapper,
                description="Performs active vulnerability scanning (XSS/SQLi) on the current page. Input: 'scan' (or empty)."
            ),
             Tool(
                name="SecurityPassiveScan",
                func=passive_scan_wrapper,
                coroutine=passive_scan_wrapper,
                description="Analyzes security headers and cookies for a URL. Input: The URL to analyze."
            )
        ]
