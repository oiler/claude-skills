# API Security

## Rate Limiting

All public-facing endpoints should have rate limits to prevent brute force, scraping, and denial of service.

**WordPress:**
```php
function check_rate_limit() {
    $ip = $_SERVER['REMOTE_ADDR'];
    $key = 'rate_limit_' . $ip;  // Don't use md5 — it adds nothing here
    $count = get_transient($key) ?: 0;

    if ($count > 100) {
        wp_send_json_error('Rate limit exceeded', 429);
    }
    set_transient($key, $count + 1, HOUR_IN_SECONDS);
}
```

**Django:**
```python
# Using django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', block=True)
def api_view(request):
    pass

# Django REST Framework throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '50/hour',
        'user': '200/hour',
    }
}
```

**FastAPI:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/data")
@limiter.limit("100/hour")
async def get_data(request: Request):
    pass

# Stricter limits for auth endpoints
@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request):
    pass
```

**Laravel:**
```php
// routes/api.php — built-in rate limiting
Route::middleware('throttle:100,60')->group(function () {
    Route::get('/data', [DataController::class, 'index']);
});

// Custom rate limiter in RouteServiceProvider
RateLimiter::for('login', function (Request $request) {
    return Limit::perMinute(10)->by($request->ip());
});
```

## API Authentication

**Never send API keys in query parameters** (they get logged in URLs, referrers, proxy logs):

```python
# WRONG - Key in URL
GET /api/data?api_key=sk_live_123

# RIGHT - Key in header
GET /api/data
Authorization: Bearer sk_live_123
```

**Store keys in environment variables:**
```python
# WRONG
api_key = "sk_live_123456789"

# RIGHT
import os
api_key = os.environ.get('API_KEY')
# Or use python-decouple, django-environ, etc.
```

## Input Validation

Validate all API inputs — type, range, format, and length:

**FastAPI (Pydantic does this well):**
```python
from pydantic import BaseModel, Field, EmailStr, constr

class CreateUser(BaseModel):
    username: constr(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    age: int = Field(ge=13, le=150)

@app.post("/users")
async def create_user(user: CreateUser):
    pass  # Input is already validated
```

**Django REST Framework:**
```python
from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=50)
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=13, max_value=150)
```

**Laravel:**
```php
$validated = $request->validate([
    'username' => 'required|string|min:3|max:50|alpha_dash',
    'email' => 'required|email',
    'age' => 'required|integer|min:13|max:150',
]);
```

## Mass Assignment Protection

Prevent users from setting fields they shouldn't by explicitly declaring which fields are fillable:

**Laravel:**
```php
class User extends Model {
    // Only these fields can be set via mass assignment
    protected $fillable = ['name', 'email'];
    // Or block specific fields
    protected $guarded = ['is_admin', 'role'];
}

// WRONG — allows any field
User::create($request->all());

// RIGHT — only allowed fields
User::create($request->only(['name', 'email']));
```

**Django:**
```python
# Forms automatically handle this via declared fields
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email']  # Only these are accepted
        # Never use fields = '__all__' on user-facing forms
```

**FastAPI:**
```python
# Pydantic models naturally restrict fields
class UserCreate(BaseModel):
    name: str
    email: str
    # is_admin is NOT here, so it can't be set via API

class UserInternal(UserCreate):
    is_admin: bool = False  # Only used internally
```

## SSRF (Server-Side Request Forgery) Prevention

SSRF occurs when an attacker can make your server send requests to internal resources (cloud metadata, internal APIs, databases).

**Vulnerable pattern:**
```python
# WRONG - User controls the URL your server fetches
@app.post("/fetch-url")
async def fetch_url(url: str):
    response = requests.get(url)  # Attacker sends: http://169.254.169.254/latest/meta-data/
    return response.text
```

**Prevention:**
```python
from urllib.parse import urlparse
import ipaddress, socket

BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),  # AWS metadata
    ipaddress.ip_network('0.0.0.0/8'),
]

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)

    # Only allow http/https
    if parsed.scheme not in ('http', 'https'):
        return False

    # Resolve hostname and check against blocked networks
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    except (socket.gaierror, ValueError):
        return False

    for network in BLOCKED_NETWORKS:
        if ip in network:
            return False

    return True

@app.post("/fetch-url")
async def fetch_url(url: str):
    if not is_safe_url(url):
        raise HTTPException(400, "URL not allowed")
    response = requests.get(url, timeout=5)
    return response.text
```

**Best practices:**
- Allowlist permitted domains when possible
- Block private IP ranges and cloud metadata endpoints
- Set timeouts on outbound requests
- Don't follow redirects blindly (they can redirect to internal IPs)
- Use network-level controls (firewall rules) as defense in depth

## Error Handling in APIs

```python
# WRONG - Exposes internal details
@app.exception_handler(Exception)
async def handler(request, exc):
    return JSONResponse({"error": str(exc), "traceback": traceback.format_exc()})

# RIGHT - Generic error in production
@app.exception_handler(Exception)
async def handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)  # Log details
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred"}  # Generic response
    )
```
