import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quantum_qe_core.skills.scanner import SecurityAuditor

def test_scan_headers_missing():
    auditor = SecurityAuditor()
    url = "http://example.com"
    headers = {
        "Content-Type": "text/html"
    }
    auditor.scan_headers(url, headers)
    findings = auditor.get_findings()
    
    # Required headers are: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
    # Only Content-Type is provided, so 5 findings should be present.
    assert len(findings) == 5
    types = [f['type'] for f in findings]
    assert all(t == "Missing Header" for t in types)

def test_scan_headers_present():
    auditor = SecurityAuditor()
    url = "http://example.com"
    headers = {
        "Content-Security-Policy": "default-src 'self'",
        "Strict-Transport-Security": "max-age=31536000",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer"
    }
    auditor.scan_headers(url, headers)
    findings = auditor.get_findings()
    assert len(findings) == 0

def test_scan_cookies_insecure():
    auditor = SecurityAuditor()
    cookies = [
        {
            "name": "session",
            "secure": False,
            "httpOnly": False,
            "sameSite": "None"
        }
    ]
    auditor.scan_cookies(cookies)
    findings = auditor.get_findings()
    
    # Expected: 3 findings (Secure, HttpOnly, SameSite)
    assert len(findings) == 3
    
    details = [f['details'] for f in findings]
    assert any("missing the 'Secure' flag" in d for d in details)
    assert any("missing the 'HttpOnly' flag" in d for d in details)
    assert any("has weak 'SameSite' policy (none)" in d for d in details)

def test_scan_cookies_secure():
    auditor = SecurityAuditor()
    cookies = [
        {
            "name": "session",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        }
    ]
    auditor.scan_cookies(cookies)
    findings = auditor.get_findings()
    assert len(findings) == 0

def test_scan_cookies_samesite_casing():
    auditor = SecurityAuditor()
    cookies = [
        {
            "name": "c1",
            "secure": True,
            "httpOnly": True,
            "sameSite": "none"
        },
        {
            "name": "c2",
            "secure": True,
            "httpOnly": True,
            "sameSite": "NONE"
        },
         {
            "name": "c3",
            "secure": True,
            "httpOnly": True,
            "sameSite": ""
        }
    ]
    auditor.scan_cookies(cookies)
    findings = auditor.get_findings()
    
    # Each cookie should trigger a SameSite finding
    assert len(findings) == 3
    for finding in findings:
        assert "has weak 'SameSite' policy" in finding['details']
