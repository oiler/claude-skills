---
name: web-security
description: Application-level security best practices for web development. Use when writing or reviewing code in WordPress, Laravel, Django, or FastAPI to prevent XSS, SQL injection, and other common attack vectors. Covers input sanitization, output escaping, secure data handling, PII protection, and framework-specific security patterns.
---

# Web Security Best Practices

Application-level security guidance for building secure web applications in WordPress (PHP), Laravel (PHP), Django (Python), and FastAPI (Python).

## Core Security Principles

### Defense in Depth
- Never trust user input - validate and sanitize everything
- Escape output appropriately for context (HTML, JS, SQL, URL)
- Use framework security features - don't roll your own
- Principle of least privilege for database users and file permissions
- Fail securely - errors shouldn't expose sensitive information

### OWASP Top 10 Focus Areas
1. Injection attacks (SQL, XSS, Command)
2. Broken authentication
3. Sensitive data exposure
4. XML External Entities (XXE)
5. Broken access control
6. Security misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure deserialization
9. Using components with known vulnerabilities
10. Insufficient logging and monitoring

## XSS (Cross-Site Scripting) Prevention

### Understanding XSS Types
- **Stored XSS**: Malicious script stored in database, executed when retrieved
- **Reflected XSS**: Malicious script in URL parameters, reflected back in response
- **DOM-based XSS**: Client-side script manipulation without server involvement

### WordPress XSS Prevention

**Always escape output based on context:**

```php
// HTML context
echo esc_html($user_input);

// HTML attribute context
echo '<div class="' . esc_attr($user_class) . '">';

// URL context
echo '<a href="' . esc_url($user_url) . '">';

// JavaScript context
echo '<script>var data = ' . wp_json_encode($user_data) . ';</script>';

// Textarea context
echo '<textarea>' . esc_textarea($user_text) . '</textarea>';
```

**Anti-pattern - Never do this:**
```php
// WRONG - Direct output without escaping
echo $_POST['user_input'];
echo $wpdb->get_var("SELECT meta_value FROM ...");
```

**Sanitize input on save:**
```php
// Sanitize before storing
$clean_text = sanitize_text_field($_POST['text']);
$clean_email = sanitize_email($_POST['email']);
$clean_url = esc_url_raw($_POST['url']);
$clean_html = wp_kses_post($_POST['content']); // Allow safe HTML
```

### Django XSS Prevention

**Template auto-escaping (enabled by default):**
```django
{# Automatically escaped #}
{{ user_input }}

{# Mark as safe only if you've sanitized it #}
{{ trusted_html|safe }}

{# Escape in JavaScript context #}
<script>
var data = "{{ user_input|escapejs }}";
</script>
```

**Python code escaping:**
```python
from django.utils.html import escape, format_html

# Manual escaping
safe_output = escape(user_input)

# Safe HTML construction
html = format_html('<a href="{}">{}</a>', url, escape(text))
```

**Anti-pattern:**
```python
# WRONG - Marking untrusted content as safe
return mark_safe(request.POST['content'])

# WRONG - Disabling auto-escaping
{% autoescape off %}{{ user_content }}{% endautoescape %}
```

### Laravel XSS Prevention

**Blade templates auto-escape:**
```php
{{-- Automatically escaped --}}
{{ $user_input }}

{{-- Unescaped (use with extreme caution) --}}
{!! $trusted_html !!}

{{-- JavaScript context --}}
<script>
var data = @json($user_data);
</script>
```

**PHP escaping:**
```php
// Use Laravel helpers
e($user_input); // Equivalent to htmlspecialchars()

// Or native PHP
htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');
```

### FastAPI XSS Prevention

**Jinja2 templates auto-escape:**
```html
{# Automatically escaped #}
{{ user_input }}

{# Mark as safe only if sanitized #}
{{ trusted_html|safe }}
```

**Python code:**
```python
from html import escape

# Manual escaping
safe_output = escape(user_input)
```

### JavaScript XSS Prevention

**Never use innerHTML with user input:**
```javascript
// WRONG - Vulnerable to XSS
element.innerHTML = userInput;

// RIGHT - Safe text insertion
element.textContent = userInput;

// RIGHT - For HTML, sanitize first
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

**Safe DOM manipulation:**
```javascript
// Create elements safely
const div = document.createElement('div');
div.textContent = userInput; // Automatically escaped
div.setAttribute('data-user', userValue); // Safe for attributes

// Event handlers - avoid eval-like patterns
// WRONG
element.onclick = new Function(userInput);

// RIGHT
element.addEventListener('click', () => {
  // Your code here
});
```

## SQL Injection Prevention

### WordPress SQL Security

**Always use prepared statements:**
```php
global $wpdb;

// RIGHT - Using prepare()
$results = $wpdb->get_results($wpdb->prepare(
    "SELECT * FROM {$wpdb->posts} WHERE post_author = %d AND post_status = %s",
    $user_id,
    $status
));

// RIGHT - Multiple placeholders
$wpdb->query($wpdb->prepare(
    "UPDATE {$wpdb->postmeta} SET meta_value = %s WHERE post_id = %d AND meta_key = %s",
    $new_value,
    $post_id,
    $meta_key
));
```

**Anti-pattern:**
```php
// WRONG - Direct variable interpolation
$wpdb->query("SELECT * FROM {$wpdb->posts} WHERE ID = {$_GET['id']}");

// WRONG - Using esc_sql() alone (not sufficient)
$wpdb->query("SELECT * FROM posts WHERE title = '" . esc_sql($_POST['title']) . "'");
```

**Use WP_Query when possible:**
```php
// Safer high-level API
$query = new WP_Query([
    'author' => $user_id,
    'post_status' => $status,
    'meta_query' => [
        [
            'key' => $meta_key,
            'value' => $meta_value
        ]
    ]
]);
```

### Django SQL Security

**ORM is safe by default:**
```python
# RIGHT - ORM automatically parameterizes
User.objects.filter(username=user_input)
Post.objects.filter(author_id=user_id, status=status)

# RIGHT - Using Q objects
from django.db.models import Q
User.objects.filter(Q(username=search) | Q(email=search))
```

**Raw queries - use parameters:**
```python
# RIGHT - Parameterized raw query
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM users WHERE username = %s", [user_input])

# WRONG - String formatting
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
```

### Laravel SQL Security

**Eloquent ORM is safe:**
```php
// RIGHT - Query builder with bindings
DB::table('users')
    ->where('email', $email)
    ->where('status', $status)
    ->get();

// RIGHT - Eloquent models
User::where('email', $email)->first();
```

**Raw queries - use bindings:**
```php
// RIGHT - Named bindings
DB::select('SELECT * FROM users WHERE email = :email', ['email' => $email]);

// RIGHT - Positional bindings
DB::select('SELECT * FROM users WHERE email = ?', [$email]);

// WRONG - String concatenation
DB::select("SELECT * FROM users WHERE email = '{$email}'");
```

### FastAPI SQL Security

**SQLAlchemy ORM is safe:**
```python
# RIGHT - ORM with parameters
session.query(User).filter(User.username == user_input).first()

# RIGHT - Using parameters
session.execute(
    text("SELECT * FROM users WHERE username = :username"),
    {"username": user_input}
)

# WRONG - String formatting
session.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
```

## Authentication & Session Security

### WordPress Authentication

**Use nonces for form submissions:**
```php
// Generate nonce in form
wp_nonce_field('my_action', 'my_nonce');

// Verify nonce on submission
if (!isset($_POST['my_nonce']) || !wp_verify_nonce($_POST['my_nonce'], 'my_action')) {
    wp_die('Security check failed');
}
```

**Check user capabilities:**
```php
// Always verify permissions
if (!current_user_can('edit_posts')) {
    wp_die('Unauthorized');
}

// For AJAX actions
check_ajax_referer('my_action', 'nonce');
```

**Secure password handling:**
```php
// WordPress handles this - never store plain passwords
// Use wp_set_password() or wp_hash_password()
wp_set_password($new_password, $user_id);
```

### Django Authentication

**CSRF protection (enabled by default):**
```django
{# In forms #}
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

```python
# Exempt view from CSRF (use carefully)
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def my_view(request):
    # Only for APIs with token auth
    pass
```

**Permission checks:**
```python
from django.contrib.auth.decorators import login_required, permission_required

@login_required
def my_view(request):
    # User must be authenticated
    pass

@permission_required('app.change_model')
def admin_view(request):
    # User must have specific permission
    pass
```

**Password handling:**
```python
from django.contrib.auth.hashers import make_password, check_password

# Never store plain passwords - Django handles this
user.set_password(raw_password)  # Automatically hashes
user.save()
```

### Laravel Authentication

**CSRF protection (enabled by default):**
```php
{{-- In Blade templates --}}
<form method="POST">
    @csrf
    <!-- form fields -->
</form>
```

**Authorization checks:**
```php
// Middleware
Route::get('/admin', function () {
    // ...
})->middleware('auth');

// Manual checks
if (!Auth::check()) {
    return redirect('login');
}

// Gate authorization
if (Gate::denies('update-post', $post)) {
    abort(403);
}
```

### FastAPI Authentication

**Dependency injection for auth:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
```

## Secure Data Handling

### PII (Personally Identifiable Information)

**Storage best practices:**
- Encrypt sensitive data at application level when needed
- Never log PII (emails, passwords, SSNs, credit cards)
- Use hashed/tokenized references when possible
- Implement data retention policies

**WordPress PII handling:**
```php
// Don't log sensitive data
error_log("User login: {$username}"); // OK
error_log("Password: {$password}"); // NEVER DO THIS

// Sanitize before storage
$user_data = [
    'email' => sanitize_email($_POST['email']),
    'phone' => preg_replace('/[^0-9]/', '', $_POST['phone']),
];
```

**Django PII handling:**
```python
import logging

logger = logging.getLogger(__name__)

# Don't log sensitive data
logger.info(f"User {user.username} logged in")  # OK
logger.info(f"Password: {password}")  # NEVER DO THIS

# Use select_related carefully to avoid exposing relations
User.objects.select_related('profile').only('username', 'email')
```

### E-commerce Security

**Never store credit card data directly:**
- Use payment processors (Stripe, PayPal, etc.)
- Store only tokenized references
- Never log full credit card numbers

**WordPress/WooCommerce:**
```php
// Let payment gateways handle sensitive data
// Store only tokens and transaction IDs
update_post_meta($order_id, '_transaction_id', sanitize_text_field($transaction_id));

// Never store CVV
// Never store full card numbers (only last 4 digits if needed)
```

**Django payment handling:**
```python
# Use payment library, never handle cards directly
import stripe

# Store only references
class Order(models.Model):
    stripe_payment_intent_id = models.CharField(max_length=255)
    # Never: credit_card_number, cvv, etc.
```

## File Upload Security

### Validation Requirements

**Always validate:**
- File type (MIME type and extension)
- File size limits
- File name (sanitize and rename)
- Content scanning for malware

### WordPress File Uploads

```php
// Validate file type
$allowed_types = ['image/jpeg', 'image/png', 'application/pdf'];
if (!in_array($_FILES['file']['type'], $allowed_types)) {
    wp_die('Invalid file type');
}

// Use WordPress upload handler
$upload = wp_handle_upload($_FILES['file'], [
    'test_form' => false,
    'mimes' => [
        'jpg|jpeg' => 'image/jpeg',
        'png' => 'image/png',
        'pdf' => 'application/pdf'
    ]
]);

// Store outside web root when possible
// Rename files to prevent path traversal
$safe_filename = sanitize_file_name($_FILES['file']['name']);
```

### Django File Uploads

```python
from django.core.files.storage import default_storage
from django.core.validators import FileExtensionValidator

class DocumentForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])]
    )

def handle_upload(request):
    form = DocumentForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = form.cleaned_data['file']
        
        # Validate MIME type
        if uploaded_file.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
            return HttpResponse('Invalid file type', status=400)
        
        # Save with secure filename
        filename = default_storage.save(
            f'uploads/{uuid.uuid4()}.{uploaded_file.name.split(".")[-1]}',
            uploaded_file
        )
```

### Laravel File Uploads

```php
// Validate in request
$request->validate([
    'file' => 'required|file|mimes:jpeg,png,pdf|max:2048'
]);

// Store with random name
$path = $request->file('file')->store('uploads', 'private');

// Never trust user-provided filename
$safe_path = Storage::putFileAs(
    'uploads',
    $request->file('file'),
    Str::random(40) . '.' . $request->file('file')->extension()
);
```

## API Security

### Rate Limiting

**WordPress:**
```php
// Implement rate limiting for API endpoints
function check_rate_limit($ip) {
    $transient_key = 'rate_limit_' . md5($ip);
    $count = get_transient($transient_key);
    
    if ($count && $count > 100) {
        wp_die('Rate limit exceeded', 429);
    }
    
    set_transient($transient_key, ($count ?? 0) + 1, HOUR_IN_SECONDS);
}
```

**Django:**
```python
# Use django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h')
def api_view(request):
    pass
```

**FastAPI:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/endpoint")
@limiter.limit("100/hour")
async def endpoint(request: Request):
    pass
```

### API Authentication

**Token-based auth patterns:**
```python
# FastAPI with Bearer tokens
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/data")
async def get_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_token(token)
    return {"data": "protected"}
```

**Never expose API keys:**
```python
# WRONG - Hardcoded
api_key = "sk_live_123456789"

# RIGHT - Environment variables
import os
api_key = os.environ.get('API_KEY')
```

## Environment & Configuration Security

### Secrets Management

**Never commit secrets to version control:**
```python
# Use .env files (add to .gitignore)
# Django settings.py
import os
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DATABASE_PASSWORD = config('DB_PASSWORD')
API_KEY = config('API_KEY')
```

```php
// WordPress wp-config.php
define('DB_PASSWORD', getenv('DB_PASSWORD'));
define('AUTH_KEY', getenv('AUTH_KEY'));
```

### Debug Mode

**Disable debug in production:**
```python
# Django
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
```

```php
// WordPress
define('WP_DEBUG', false);
define('WP_DEBUG_DISPLAY', false);
```

## Code Review Checklist

When reviewing code for security:

**Input/Output:**
- [ ] All user input sanitized before storage
- [ ] All output escaped for appropriate context
- [ ] No direct echo/print of user data without escaping

**Database:**
- [ ] All queries use prepared statements or ORM
- [ ] No string concatenation in SQL queries
- [ ] Proper parameter binding

**Authentication:**
- [ ] CSRF tokens present on forms
- [ ] Nonces verified in WordPress
- [ ] Permission checks before sensitive operations
- [ ] No passwords in logs or error messages

**File Operations:**
- [ ] File uploads validated (type, size, content)
- [ ] Filenames sanitized
- [ ] Files stored outside web root when possible

**API/AJAX:**
- [ ] Rate limiting implemented
- [ ] Authentication required for sensitive endpoints
- [ ] Input validation on all parameters

**Configuration:**
- [ ] No hardcoded secrets
- [ ] Debug mode disabled in production
- [ ] Error messages don't expose system details

## Common Anti-Patterns to Avoid

1. **Trusting client-side validation alone** - Always validate server-side
2. **Using blacklists instead of whitelists** - Prefer allowing known-good over blocking known-bad
3. **Rolling your own crypto** - Use proven libraries and frameworks
4. **Exposing detailed error messages** - Generic errors in production
5. **Ignoring framework security features** - Use built-in protections
6. **Security through obscurity** - Don't rely on hiding implementation details
7. **Not updating dependencies** - Keep frameworks and libraries current

## Testing Security

### Manual Testing Approaches

**Test for XSS:**
```
# Common XSS payloads to test
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
```

**Test for SQL Injection:**
```
# Test input fields with
' OR '1'='1
'; DROP TABLE users--
1' UNION SELECT NULL--
```

**Test file uploads:**
- Upload files with double extensions (file.php.jpg)
- Upload files with null bytes (file.php%00.jpg)
- Upload executable files
- Upload oversized files

### Automated Security Testing

**WordPress:**
- WPScan - vulnerability scanner
- Wordfence - security plugin with scanner

**Python:**
- Bandit - security linter for Python
- Safety - checks dependencies for vulnerabilities

**PHP:**
- PHPCS with security standards
- Psalm/PHPStan with security plugins

**General:**
- OWASP ZAP - web application scanner
- Burp Suite - security testing platform
