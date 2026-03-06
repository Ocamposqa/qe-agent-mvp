# Security Testing Framework (OWASP Top 10)

The Quantum QE `Auditor` Agent conducts security verification against the target web application dynamically after the primary `Navigator` finishes the functional interactions.

The framework divides testing into two major phases: **Passive Analysis** and **Active Scanning**.

---

## 1. Passive Analysis (Reconnaissance)

During the functional navigation phase, the Playwright Context stealthily logs all Network Traffic, HTTP Response Headers, and Cookies without sending explicit malicious payloads.

### Checked Vulnerabilities:
* **Insecure Cookies (A05:2021 Security Misconfiguration):**
  * Checks if `HttpOnly` is missing (Session hijacking via XSS).
  * Checks if `Secure` flag is missing (Session hijacking via Man-In-The-Middle/HTTP).
* **Missing Security Headers (A05:2021):**
  * **Strict-Transport-Security (HSTS):** Missing header allows protocol downgrade attacks.
  * **Content-Security-Policy (CSP):** Missing header permits inline script execution (XSS).
  * **X-Frame-Options:** Missing header allows Clickjacking attacks via iframes.
  * **X-Content-Type-Options:** Missing `nosniff` allows MIME-sniffing execution.

---

## 2. Active Scanning (Exploitation)

Once the DOM state is fully rendered and the passive analysis is concluded, the `Auditor` agent actively inspects input fields and URL parameters to test for injection flaws.

### Checked Vulnerabilities:
* **Cross-Site Scripting (XSS) (A03:2021 Injection):**
  * The agent analyzes all `<input>`, `<textarea>`, and URL query parameters.
  * *Test:* Injects benign payloads like `<script>alert('Quantum')</script>` or `" onload="alert(1)` to verify if the DOM reflects unescaped user input.
* **SQL Injection (SQLi) (A03:2021 Injection):**
  * The agent tests login forms and search bars with basic SQL tautologies.
  * *Test:* Injects payloads like `' OR 1=1 --` to check for database syntax errors or authentication bypasses in the HTTP response.
* **Sensitive Data Exposure (A02:2021 Cryptographic Failures):**
  * The agent searches the final rendered DOM for accidentally exposed PII (Social Security Numbers, Credit Cards) or developer secrets (API Keys, `aws_access_key`) leaked into the client side.

---

## Output & Handoff
If any vulnerabilities are confirmed, the `Auditor` agent structures a JSON response detailing the `Severity`, `CVSS Score` estimate, `Location` (XPath/Header), and `Remediation` steps. This structured data is fed directly to the `Reporter` agent for markdown/PDF PDF generation.
