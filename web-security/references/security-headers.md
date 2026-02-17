# Security Headers

Security headers are HTTP response headers that instruct browsers to enable security protections. They are among the highest-impact, lowest-effort security improvements for any web application.

## Content-Security-Policy (CSP)

CSP prevents XSS and data injection by restricting which sources can load scripts, styles, images, and other resources.

### Recommended Starting Policy

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

**Directive reference:**
- `default-src 'self'` — Fallback for all resource types, only allow same origin
- `script-src 'self'` — Only load scripts from same origin (add CDN domains as needed)
- `style-src 'self' 'unsafe-inline'` — Allow inline styles (many frameworks need this)
- `img-src 'self' data: https:` — Allow images from same origin, data URIs, and HTTPS
- `connect-src 'self'` — Restrict AJAX/fetch/WebSocket to same origin
- `frame-ancestors 'none'` — Prevent clickjacking (replaces X-Frame-Options)
- `base-uri 'self'` — Prevent base tag injection
- `form-action 'self'` — Restrict form submission targets

### Framework Implementation

**WordPress:**
```php
// In functions.php or a security plugin
add_action('send_headers', function() {
    header("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';");
});

// Or in .htaccess
// Header set Content-Security-Policy "default-src 'self'; ..."
```

Note: WordPress core and many plugins require `'unsafe-inline'` and `'unsafe-eval'` for scripts. Use nonce-based CSP for stricter policies:
```php
// Generate nonce per request
$csp_nonce = base64_encode(random_bytes(16));
header("Content-Security-Policy: script-src 'nonce-{$csp_nonce}' 'strict-dynamic';");
// Add nonce to script tags: <script nonce="<?php echo $csp_nonce; ?>">
```

**Django:**
```python
# Using django-csp package (recommended)
# pip install django-csp
# settings.py
MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    # ...
]
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Or manually in middleware/views
from django.http import HttpResponse
response['Content-Security-Policy'] = "default-src 'self'; ..."
```

**Laravel:**
```php
// Middleware approach
class SecurityHeaders {
    public function handle($request, Closure $next) {
        $response = $next($request);
        $response->headers->set('Content-Security-Policy',
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-ancestors 'none';"
        );
        return $response;
    }
}

// Register in app/Http/Kernel.php
protected $middleware = [
    \App\Http\Middleware\SecurityHeaders::class,
];
```

**FastAPI:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "frame-ancestors 'none';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

**Plotly Dash:**
Dash heavily uses inline scripts and eval for callbacks. A strict CSP will break Dash. Use a permissive policy:
```python
from flask import Flask

server = Flask(__name__)
app = dash.Dash(__name__, server=server)

@server.after_request
def add_security_headers(response):
    # Dash requires unsafe-inline and unsafe-eval for script-src
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    return response
```

### CSP Reporting

Use `report-uri` or `report-to` to receive violation reports without blocking (useful for rollout):
```
Content-Security-Policy-Report-Only: default-src 'self'; report-uri /csp-report
```

## Strict-Transport-Security (HSTS)

Forces browsers to use HTTPS for all future requests to the domain.

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

- `max-age=63072000` — Remember for 2 years
- `includeSubDomains` — Apply to all subdomains
- `preload` — Submit to browser preload lists (permanent, be careful)

**Implementation is the same across frameworks** — set the header in middleware or web server config. Django has a built-in setting:
```python
# Django settings.py
SECURE_HSTS_SECONDS = 63072000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
```

## CORS (Cross-Origin Resource Sharing)

Controls which external origins can access your API. Misconfigured CORS is a common vulnerability.

### Rules

- Never use `Access-Control-Allow-Origin: *` on authenticated endpoints
- Never reflect the Origin header without validation
- Restrict allowed methods and headers
- Be explicit about allowed origins

**Django:**
```python
# pip install django-cors-headers
INSTALLED_APPS = ['corsheaders', ...]
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', ...]

# Explicit origins only
CORS_ALLOWED_ORIGINS = [
    "https://yourfrontend.com",
    "https://admin.yourfrontend.com",
]
CORS_ALLOW_CREDENTIALS = True  # Only if needed for cookies
```

**Laravel:**
```php
// config/cors.php
return [
    'paths' => ['api/*'],
    'allowed_origins' => ['https://yourfrontend.com'],
    'allowed_methods' => ['GET', 'POST', 'PUT', 'DELETE'],
    'allowed_headers' => ['Content-Type', 'Authorization'],
    'supports_credentials' => true,
];
```

**FastAPI:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"],  # Never ["*"] with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Plotly Dash:**
Dash is typically served as a single application (frontend + backend together), so CORS is usually not needed. If you add API routes that external frontends need:
```python
from flask_cors import CORS
# Only on specific routes, not the whole app
CORS(app.server, resources={r"/api/*": {"origins": "https://yourfrontend.com"}})
```

**Anti-patterns:**
```python
# WRONG - Reflects any origin (defeats the purpose of CORS)
origin = request.headers.get('Origin')
response.headers['Access-Control-Allow-Origin'] = origin

# WRONG - Wildcard with credentials
allow_origins=["*"],
allow_credentials=True,  # Browsers will reject this, but it shows bad intent
```

## Other Essential Headers

Set all of these in middleware or web server config:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

**X-Content-Type-Options: nosniff** — Prevents browsers from MIME-sniffing responses away from the declared content type. Stops attacks where a file is uploaded as .jpg but contains JavaScript.

**X-Frame-Options: DENY** — Prevents your site from being embedded in iframes (clickjacking protection). Use `SAMEORIGIN` if you need to iframe your own pages. Prefer CSP `frame-ancestors` as the modern replacement.

**Referrer-Policy: strict-origin-when-cross-origin** — Controls how much referrer information is sent. Prevents leaking full URLs (with query params, tokens) to external sites.

**Permissions-Policy** — Disables browser features you don't use, reducing attack surface.

## Quick Server Config

**Nginx:**
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
# CSP added per-application
```

**Apache (.htaccess):**
```apache
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
```

## Verification

Test your headers at: securityheaders.com or observatory.mozilla.org
