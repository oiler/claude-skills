# web-security CHANGELOG

## v1.1.0 — 2026-05-24

### Structural

- Moved this changelog out of the skill folder (was `web-security/NOTES.md`, now a sibling at `web-security-CHANGELOG.md`) — keeps the skill folder limited to `SKILL.md`, `references/`, `scripts/`, `assets/` per the workshop convention
- Added `metadata.version`, `metadata.category`, `metadata.tags` to frontmatter
- Rewrote SKILL.md "Important" section as "Core principles" with WHY-framed one-liners — every rule now explains the reasoning behind it instead of asserting it as a flat MUST
- Deduplicated the Common Anti-Patterns section (removed items already covered by Core principles)
- Updated description to include trigger phrases for the three new threat areas

### New coverage

- `references/command-injection.md` — Python (subprocess, shell=True, eval/exec), PHP (shell_exec family, escapeshell* limits), Laravel Symfony Process, allowlist patterns, the canonical Plotly Dash callback variant
- `references/path-traversal.md` — the resolve + verify-inside-base canonical defense, per-framework implementations (Django/FastAPI/Dash pathlib, WordPress sanitize_file_name + ABSPATH, Laravel realpath + Storage facade), the classic include-vuln pattern, and an explicit note that storage-location is a separate concern from traversal defense (storing uploads outside the web root)
- `references/password-policy.md` — NIST SP 800-63B rev 4 (Aug 2024) summary, HIBP k-anonymity in Python and PHP, framework storage details (WP phpass, Laravel Hash::make/argon2id, Django PBKDF2/argon2, FastAPI passlib), login-flow protections, an explicit "what NOT to do" list, and a brief 2FA/MFA pointer (deferred to a future reference)

### Eval-driven improvements

The above was iterated using `/skill-creator`'s eval loop. Iteration 1 results: new skill 95% pass rate vs. old 86%, with lower variance (stddev 0.08 vs. 0.14). Wins concentrated in the two evals where new content was relevant — Django path-traversal review (+15 pp) and FastAPI command-injection review (+14 pp). The "store outside web root" regression caught during eval was patched by adding the explicit-separate-concern section to `path-traversal.md`.

### Not addressed in this release

- 2FA/MFA implementation (its own future reference)
- WebSocket security
- NoSQL injection (unlikely to be relevant for the current target stacks)
- Subresource Integrity (SRI)

---

## v1.0.0 — 2026-02-17

### Structural fixes

- Renamed to `SKILL.md` (was `web-security-SKILL.md` — Claude couldn't discover it)
- Restructured into `SKILL.md` + 10 reference files — `SKILL.md` is now 570 words (was 770 lines in one file). References load only when the specific topic is relevant, saving context window.

### Content fixes

- Updated OWASP Top 10 to 2021 (was 2017 — XXE removed, SSRF/Insecure Design/Data Integrity added)
- Fixed WordPress MIME type check — flagged the `$_FILES['type']` spoofing issue, added `wp_check_filetype_and_ext()` and `finfo_file()`/`python-magic` for server-side validation
- Removed `md5()` from rate limiting key — was misleading about md5 in security contexts

### New coverage

- Security headers (entirely new) — CSP with framework-specific implementation and Dash caveats, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, plus Nginx/Apache configs
- Session/cookie/JWT security (entirely new) — Cookie flags (HttpOnly, Secure, SameSite), session fixation prevention, session timeout patterns, JWT algorithm confusion attacks, refresh token patterns, client-side storage risks
- Plotly Dash added across all references — callback input trust issues, `dangerously_set_inner_html` risks, `dcc.Store` data exposure, CSP compatibility (requires `unsafe-inline`/`unsafe-eval`), Flask-Login integration, CSRF design decisions
- SSRF prevention with IP blocklist pattern
- IDOR with ownership verification examples
- Mass assignment protection across frameworks
- Dependency auditing commands for pip, composer, npm
- Security logging guidance (what to log vs. what never to log)
