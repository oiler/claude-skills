# Notes


## Updates

### v1.0.0
**17 Feb 2026**

#### Structural fixes

Renamed to SKILL.md (was web-security-SKILL.md — Claude couldn't discover it)
Restructured into SKILL.md + 10 reference files — SKILL.md is now 570 words (was 770 lines in one file). References load only when the specific topic is relevant, saving context window.

#### Content fixes

Updated OWASP Top 10 to 2021 (was 2017 — XXE removed, SSRF/Insecure Design/Data Integrity added)
Fixed WordPress MIME type check — flagged the $_FILES['type'] spoofing issue, added wp_check_filetype_and_ext() and finfo_file()/python-magic for server-side validation
Removed md5() from rate limiting key — was misleading about md5 in security contexts

#### New coverage added

Security headers (entirely new) — CSP with framework-specific implementation and Dash caveats, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, plus Nginx/Apache configs
Session/cookie/JWT security (entirely new) — Cookie flags (HttpOnly, Secure, SameSite), session fixation prevention, session timeout patterns, JWT algorithm confusion attacks, refresh token patterns, client-side storage risks
Plotly Dash added across all references — callback input trust issues, dangerously_set_inner_html risks, dcc.Store data exposure, CSP compatibility (requires unsafe-inline/unsafe-eval), Flask-Login integration, CSRF design decisions
SSRF prevention with IP blocklist pattern
IDOR with ownership verification examples
Mass assignment protection across frameworks
Dependency auditing commands for pip, composer, npm
Security logging guidance (what to log vs. what never to log)

#### What's still not covered (potential future additions)
Command injection, path traversal, WebSocket security, 2FA/MFA implementation, NoSQL injection, Subresource Integrity (SRI), and password policy guidance (breached password lists, length vs. complexity). These could be added as additional reference files without touching the core SKILL.md.