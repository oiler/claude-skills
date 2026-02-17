---
name: web-security
description: Application-level security for web development. Use when writing, reviewing, or auditing code for security in WordPress, Laravel, Django, FastAPI, or Plotly Dash. Covers OWASP Top 10 2021, XSS prevention, SQL injection, CSRF, security headers (CSP, HSTS, CORS), session and cookie security, JWT handling, authentication, file uploads, API security, PII protection, and secure configuration. Trigger on "security review", "secure this", "harden", "vulnerability", "XSS", "injection", "CSRF", "CORS", "CSP", "security headers", "session security", "JWT", or "OWASP".
---

# Web Security Best Practices

Application-level security guidance for WordPress (PHP), Laravel (PHP), Django (Python), FastAPI (Python), and Plotly Dash (Python/Flask).

## Important

- Always treat user input as untrusted, including callback inputs in Dash
- Use framework security features instead of custom implementations
- Validate server-side even when client-side validation exists
- Fail securely — errors must not expose system details
- Keep dependencies updated and audited

## OWASP Top 10 (2021)

The current OWASP Top 10 categories that this skill addresses:

1. **A01 Broken Access Control** — See references/authentication-csrf.md
2. **A02 Cryptographic Failures** — See references/secure-data-handling.md
3. **A03 Injection** — See references/sql-injection.md, references/xss-prevention.md
4. **A04 Insecure Design** — Apply defense in depth throughout
5. **A05 Security Misconfiguration** — See references/security-headers.md, references/environment-config.md
6. **A06 Vulnerable Components** — See references/security-testing.md (dependency auditing)
7. **A07 Authentication Failures** — See references/authentication-csrf.md, references/session-cookie-jwt.md
8. **A08 Data Integrity Failures** — See references/secure-data-handling.md
9. **A09 Logging Failures** — See references/environment-config.md
10. **A10 SSRF** — See references/api-security.md

## When to Consult Each Reference

| User is working on... | Load this reference |
|---|---|
| HTML output, templates, rendering user data | references/xss-prevention.md |
| Database queries, search, filters | references/sql-injection.md |
| Login, registration, forms, permissions, CSRF | references/authentication-csrf.md |
| HTTP headers, CORS, CSP, HSTS, iframe protection | references/security-headers.md |
| Sessions, cookies, JWT tokens, "remember me" | references/session-cookie-jwt.md |
| File uploads, downloads, media handling | references/file-upload-security.md |
| REST APIs, rate limiting, tokens, SSRF | references/api-security.md |
| PII, encryption, payment data, logging | references/secure-data-handling.md |
| .env files, secrets, debug mode, deployment | references/environment-config.md |
| Security testing, scanning, code review | references/security-testing.md |

## Code Review Quick Checklist

When reviewing any code for security, verify all of the following:

**Input/Output:** All user input sanitized before storage. All output escaped for context (HTML, JS, SQL, URL). No raw echo/print of user data.

**Database:** All queries use prepared statements, ORM, or parameterized queries. No string concatenation or f-strings in SQL.

**Auth/Access:** CSRF tokens on all state-changing forms. Permission checks before sensitive operations. No passwords or tokens in logs.

**Headers:** CSP, HSTS, X-Content-Type-Options, X-Frame-Options all set. CORS restricted to required origins only.

**Sessions/Cookies:** HttpOnly, Secure, SameSite flags on cookies. Session regenerated after login. JWT expiration enforced.

**Files:** Upload type, size, and content validated server-side. Filenames sanitized. Files stored outside web root.

**API:** Rate limiting on all public endpoints. Authentication on sensitive endpoints. Input validation on all parameters.

**Config:** No hardcoded secrets. Debug mode off in production. Error messages generic in production.

**Dependencies:** No known vulnerabilities in packages. Lock files committed. Audit tools configured.

## Common Anti-Patterns

1. Trusting client-side validation alone — always validate server-side
2. Using blocklists instead of allowlists — prefer allowing known-good
3. Rolling your own crypto or auth — use proven libraries
4. Exposing detailed error messages in production
5. Ignoring framework security features that are available
6. Security through obscurity — hiding things is not protecting them
7. Not updating dependencies — known vulnerabilities get exploited fast
8. Storing sensitive data in client-accessible storage (localStorage, dcc.Store)
