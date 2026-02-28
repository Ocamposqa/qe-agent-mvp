# OWASP Top 10 - Web Application Security Risks

## A01:2021-Broken Access Control
Access control enforces policy such that users cannot act outside of their intended permissions. Failures lead to unauthorized information disclosure, modification, or destruction of all data or performing a business function outside the user's limits.
**Remediation:** Implement role-based access control (RBAC), deny by default, and log access control failures.

## A02:2021-Cryptographic Failures
Previously known as Sensitive Data Exposure. Focuses on failures related to cryptography (or lack thereof).
**Remediation:** Encrypt data at rest and in transit (TLS). Do not store sensitive data unnecessarily. Use strong algorithms (Argon2, PBKDF2).

## A03:2021-Injection
User-supplied data is not validated, filtered, or sanitized by the application.
**Remediation:** Use safe APIs (parameterized queries), validate input, and use LIMIT constraints.
**Example:** SQL Injection, Cross-Site Scripting (XSS).

## A04:2021-Insecure Design
Focuses on risks related to design flaws.
**Remediation:** Establish a secure development lifecycle, threat modeling, and secure design patterns.

## A05:2021-Security Misconfiguration
This is commonly a result of insecure default configurations, incomplete or ad hoc configurations, open cloud storage, misconfigured HTTP headers, and verbose error messages containing sensitive information.
**Remediation:** Hardening process, disable unnecessary features, use security headers (HSTS, CSP).

## A07:2021-Identification and Authentication Failures
Previously Broken Authentication.
**Remediation:** Multi-factor authentication, weak password checks, session management best practices (secure cookies).
