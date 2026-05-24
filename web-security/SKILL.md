---
name: web-security
description: Application-level security for web development. Use when writing, reviewing, or auditing code for security in WordPress, Laravel, Django, FastAPI, or Plotly Dash. Covers OWASP Top 10 2021, XSS prevention, SQL injection, command injection, path traversal, CSRF, security headers (CSP, HSTS, CORS), session and cookie security, JWT handling, authentication, password policy, file uploads, API security, PII protection, and secure configuration. Trigger on "security review", "secure this", "harden", "vulnerability", "XSS", "injection", "CSRF", "CORS", "CSP", "security headers", "session security", "JWT", "password", "auth", "path traversal", "command injection", "shell exec", or "OWASP".
metadata:
  version: 1.1.0
  category: security
  tags: [security, owasp, web, wordpress, laravel, django, fastapi, dash]
---

# Web Security Best Practices

Application-level security guidance for WordPress (PHP), Laravel (PHP), Django (Python), FastAPI (Python), and Plotly Dash (Python/Flask).

## Core principles

- **Treat all user input as untrusted, including Dash callback inputs.** Callback values look like they came from your UI dropdown, but a malicious user can send arbitrary HTTP requests with any value — the UI is just a hint, never a constraint.
- **Use framework security features instead of custom implementations.** Frameworks have years of vulnerability fixes and edge cases baked in; rolling your own crypto or auth almost always introduces new bugs.
- **Validate server-side even when client-side validation exists.** Client-side validation is for user experience; the server is the only place that's actually a security boundary.
- **Fail securely — errors must not expose system details.** Stack traces, file paths, and SQL error messages give attackers a map of your system.
- **Keep dependencies updated and audited.** Known CVEs get exploited within hours of disclosure; pin lock files and run audit tools in CI.

## OWASP Top 10 (2021)

The current OWASP Top 10 categories that this skill addresses:

1. **A01 Broken Access Control** — See references/authentication-csrf.md, references/path-traversal.md
2. **A02 Cryptographic Failures** — See references/secure-data-handling.md
3. **A03 Injection** — See references/sql-injection.md, references/xss-prevention.md, references/command-injection.md
4. **A04 Insecure Design** — Apply defense in depth throughout
5. **A05 Security Misconfiguration** — See references/security-headers.md, references/environment-config.md
6. **A06 Vulnerable Components** — See references/security-testing.md (dependency auditing)
7. **A07 Authentication Failures** — See references/authentication-csrf.md, references/session-cookie-jwt.md, references/password-policy.md
8. **A08 Data Integrity Failures** — See references/secure-data-handling.md
9. **A09 Logging Failures** — See references/environment-config.md
10. **A10 SSRF** — See references/api-security.md

## When to Consult Each Reference

| User is working on... | Load this reference |
|---|---|
| HTML output, templates, rendering user data | references/xss-prevention.md |
| Database queries, search, filters | references/sql-injection.md |
| Shell commands, subprocess, exec, system calls | references/command-injection.md |
| File paths, directory traversal, user-controlled paths | references/path-traversal.md |
| Login, registration, forms, permissions, CSRF | references/authentication-csrf.md |
| Password requirements, complexity, breach checking | references/password-policy.md |
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

**Shell/subprocess:** No `shell=True` with user input. No string concatenation into command strings. Use argument arrays.

**Filesystem:** User-supplied paths resolved and confirmed inside an allowed base directory before any open/read/write.

**Auth/Access:** CSRF tokens on all state-changing forms. Permission checks before sensitive operations. No passwords or tokens in logs.

**Passwords:** Length over complexity (NIST 800-63B). Check against breached-password lists. Bcrypt/argon2 for hashing.

**Headers:** CSP, HSTS, X-Content-Type-Options, X-Frame-Options all set. CORS restricted to required origins only.

**Sessions/Cookies:** HttpOnly, Secure, SameSite flags on cookies. Session regenerated after login. JWT expiration enforced.

**Files:** Upload type, size, and content validated server-side. Filenames sanitized. Files stored outside web root.

**API:** Rate limiting on all public endpoints. Authentication on sensitive endpoints. Input validation on all parameters.

**Config:** No hardcoded secrets. Debug mode off in production. Error messages generic in production.

**Dependencies:** No known vulnerabilities in packages. Lock files committed. Audit tools configured.

## Common Anti-Patterns

1. Using blocklists instead of allowlists — prefer allowing known-good, since attackers find creative bypasses for any "deny X" rule
2. Exposing detailed error messages in production — leaks paths, queries, library versions
3. Security through obscurity — hidden URLs and renamed admin paths are not access control
4. Storing sensitive data in client-accessible storage — localStorage, sessionStorage, and `dcc.Store` are all readable by any script running in the page
