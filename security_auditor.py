
from typing import List, Dict, Any

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

    def get_findings(self) -> List[Dict[str, Any]]:
        return self.findings
