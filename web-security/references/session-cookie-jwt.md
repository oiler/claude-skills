# Session, Cookie, and JWT Security

## Cookie Security Flags

Every cookie that stores session data, authentication tokens, or sensitive preferences must have these flags:

| Flag | Purpose | When to use |
|---|---|---|
| `HttpOnly` | Prevents JavaScript access (blocks XSS cookie theft) | Always on session/auth cookies |
| `Secure` | Only sent over HTTPS | Always in production |
| `SameSite=Lax` | Prevents CSRF by blocking cross-site requests | Default for most cookies |
| `SameSite=Strict` | Blocks cookie on ALL cross-site navigation | High-security auth cookies |
| `SameSite=None; Secure` | Allows cross-site (required for cross-origin iframes) | Only when explicitly needed |

### Framework Configuration

**WordPress:**
WordPress sets session cookies automatically. For custom cookies:
```php
// Set secure cookie
setcookie('my_cookie', $value, [
    'expires' => time() + 3600,
    'path' => '/',
    'domain' => '.yourdomain.com',
    'secure' => true,       // HTTPS only
    'httponly' => true,      // No JS access
    'samesite' => 'Lax',    // CSRF protection
]);

// WordPress auth cookie constants (wp-config.php)
define('COOKIE_DOMAIN', '.yourdomain.com');
define('FORCE_SSL_ADMIN', true);
```

**Django:**
```python
# settings.py
SESSION_COOKIE_SECURE = True        # HTTPS only
SESSION_COOKIE_HTTPONLY = True       # No JS access (default: True)
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection (default: 'Lax')
SESSION_COOKIE_AGE = 3600           # 1 hour expiry

CSRF_COOKIE_SECURE = True           # CSRF cookie over HTTPS only
CSRF_COOKIE_HTTPONLY = True          # Prevent JS access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Lax'

# For custom cookies in views
response.set_cookie(
    'my_cookie', value,
    max_age=3600, secure=True, httponly=True, samesite='Lax'
)
```

**Laravel:**
```php
// config/session.php
'secure' => env('SESSION_SECURE_COOKIE', true),
'http_only' => true,
'same_site' => 'lax',
'lifetime' => 120, // minutes
```

**FastAPI:**
```python
from starlette.responses import Response

response.set_cookie(
    key="session_id", value=token,
    max_age=3600, secure=True, httponly=True, samesite="lax"
)
```

**Plotly Dash (Flask):**
```python
# Flask server config
app.server.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
```

## Session Management

### Session Fixation Prevention

Always regenerate the session ID after authentication status changes (login, logout, privilege escalation):

```python
# Django - automatic on login, manual if needed
from django.contrib.auth import login
login(request, user)  # Automatically cycles the session key

# Manual regeneration
request.session.cycle_key()
```

```php
// Laravel - automatic on login, manual if needed
Auth::login($user);  // Regenerates session ID
session()->regenerate();  // Manual regeneration

// WordPress handles this automatically on login
```

```python
# FastAPI with custom sessions
from starlette.requests import Request

async def login_user(request: Request, user):
    # Delete old session
    request.session.clear()
    # Create new session with user data
    request.session["user_id"] = user.id
```

### Session Timeout

Implement both idle timeout (inactivity) and absolute timeout (max session duration):

```python
# Django settings.py
SESSION_COOKIE_AGE = 3600           # Absolute timeout: 1 hour
SESSION_SAVE_EVERY_REQUEST = True    # Reset idle timer on each request

# Custom idle timeout middleware
class IdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                from datetime import datetime, timedelta
                idle_limit = timedelta(minutes=30)
                if datetime.now().timestamp() - last_activity > idle_limit.total_seconds():
                    from django.contrib.auth import logout
                    logout(request)
            request.session['last_activity'] = datetime.now().timestamp()
        return self.get_response(request)
```

### Server-Side Session Storage

Avoid storing session data only in cookies (client-side sessions are tamper-prone):

```python
# Django - Use database or cache backend
SESSION_ENGINE = 'django.contrib.sessions.backends.db'       # Database
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'     # Redis/Memcached
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db' # Cache + DB fallback
```

```php
// Laravel - Use database or Redis
// config/session.php
'driver' => 'database',  // or 'redis'
```

## JWT (JSON Web Token) Security

### Token Configuration

```python
# Recommended JWT settings
import jwt
from datetime import datetime, timedelta

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=15),  # Short-lived
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, SECRET_KEY,
            algorithms=["HS256"],  # ALWAYS specify allowed algorithms
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Critical JWT Rules

**Always specify the algorithm explicitly when verifying:**
```python
# WRONG - Vulnerable to algorithm confusion attack
payload = jwt.decode(token, SECRET_KEY)

# WRONG - Accepts "none" algorithm
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "none"])

# RIGHT - Explicit algorithm
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

**Never store JWTs in localStorage** (accessible to XSS):
```javascript
// WRONG - XSS can steal this
localStorage.setItem('token', jwt);

// RIGHT - HttpOnly cookie (not accessible to JS)
// Set via server response header, not JavaScript
```

**Use short expiration with refresh tokens:**
```python
# Access token: 15 minutes
# Refresh token: 7 days, stored in HttpOnly cookie, rotated on use

def create_tokens(user_id):
    access = jwt.encode({
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }, SECRET_KEY, algorithm="HS256")

    refresh = jwt.encode({
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7),
        "type": "refresh",
        "jti": str(uuid.uuid4())  # Track for revocation
    }, SECRET_KEY, algorithm="HS256")

    return access, refresh
```

**Use strong secrets:**
```python
# WRONG
SECRET_KEY = "secret"
SECRET_KEY = "your-256-bit-secret"

# RIGHT - Generate a proper key
import secrets
SECRET_KEY = secrets.token_hex(32)  # 256-bit key

# Or for RS256 (asymmetric, recommended for multi-service architectures)
# Sign with private key, verify with public key
```

### JWT Anti-Patterns

- Storing sensitive data in JWT payload (it's base64-encoded, not encrypted)
- Not validating expiration (accepting expired tokens)
- Using the same secret across environments
- Not implementing token revocation (logout should invalidate tokens)
- Accepting tokens from query parameters (logged in URLs, referrers, proxies)

## Client-Side Storage Risks

**Never store sensitive data in browser-accessible storage:**

```javascript
// WRONG - All of these are accessible to XSS
localStorage.setItem('auth_token', token);
sessionStorage.setItem('user_data', JSON.stringify(data));
document.cookie = `token=${token}`;  // Without HttpOnly flag
```

```python
# WRONG - Dash dcc.Store is client-accessible (visible in browser DevTools)
# Never store secrets, tokens, or sensitive PII in dcc.Store
dcc.Store(id='user-data', data={'ssn': '123-45-6789'})  # NEVER

# RIGHT - Store only non-sensitive UI state
dcc.Store(id='ui-state', data={'selected_tab': 'overview'})

# For sensitive data, keep it server-side
# Use server-side caching (Flask-Caching, Redis) keyed by session ID
```
