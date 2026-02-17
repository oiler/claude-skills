# Authentication and CSRF Protection

## CSRF (Cross-Site Request Forgery)

CSRF tricks authenticated users into submitting unintended requests. Protection is required on all state-changing operations (POST, PUT, DELETE).

### WordPress

```php
// Generate nonce in form
wp_nonce_field('my_action', 'my_nonce');

// Verify nonce on submission
if (!isset($_POST['my_nonce']) || !wp_verify_nonce($_POST['my_nonce'], 'my_action')) {
    wp_die('Security check failed');
}

// For AJAX actions
check_ajax_referer('my_action', 'nonce');

// Generate nonce for JS
wp_localize_script('my-script', 'myAjax', [
    'nonce' => wp_create_nonce('my_action'),
    'url' => admin_url('admin-ajax.php')
]);
```

### Django

CSRF protection is enabled by default via middleware:
```django
{# In every form #}
<form method="post">
    {% csrf_token %}
    <!-- fields -->
</form>
```

```python
# AJAX requests need the CSRF token in headers
# In JavaScript, read from the cookie:
# const csrftoken = document.cookie.match(/csrftoken=([^;]+)/)[1];
# fetch(url, { headers: { 'X-CSRFToken': csrftoken } })

# Only exempt views that use token-based auth (not cookie auth)
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Use ONLY for API endpoints with non-cookie auth
def api_view(request):
    pass
```

### Laravel

```php
{{-- In Blade templates --}}
<form method="POST">
    @csrf
    <!-- fields -->
</form>

{{-- For AJAX, include the token in meta tag --}}
<meta name="csrf-token" content="{{ csrf_token() }}">
```

```javascript
// JavaScript: read from meta tag
const token = document.querySelector('meta[name="csrf-token"]').content;
fetch(url, { headers: { 'X-CSRF-TOKEN': token } });
```

### FastAPI

FastAPI is typically API-only with token auth (not cookies), so CSRF is less relevant. If you serve HTML forms with cookie-based sessions, add CSRF manually:

```python
# Use starlette-csrf or similar
from starlette_csrf import CSRFMiddleware

app.add_middleware(CSRFMiddleware, secret="your-secret-key")
```

### Plotly Dash

Dash intentionally removed CSRF tokens. All Dash callbacks use POST with `application/json` content type, which triggers CORS preflight checks and prevents simple cross-origin form submissions. This is considered sufficient protection per OWASP guidelines.

However, if you expose Flask routes alongside Dash:
```python
# Dash app with additional Flask routes
server = app.server

@server.route('/api/action', methods=['POST'])
def custom_action():
    # This Flask route does NOT have Dash's CSRF protection
    # Add your own protection if using cookie-based auth
    pass
```

## Permission and Access Control

### WordPress

```php
// Always check capabilities before actions
if (!current_user_can('edit_posts')) {
    wp_die('Unauthorized');
}

// Check ownership — don't just check role
$post = get_post($post_id);
if ($post->post_author != get_current_user_id() && !current_user_can('edit_others_posts')) {
    wp_die('Unauthorized');
}
```

### Django

```python
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

@login_required
def my_view(request):
    pass

@permission_required('app.change_model', raise_exception=True)
def admin_view(request):
    pass

# Object-level permissions — check ownership
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user and not request.user.has_perm('app.edit_any_post'):
        raise PermissionDenied
```

### Laravel

```php
// Middleware
Route::get('/admin', fn() => ...)->middleware('auth');

// Gate authorization
if (Gate::denies('update-post', $post)) {
    abort(403);
}

// Policy — object-level permissions
class PostPolicy {
    public function update(User $user, Post $post) {
        return $user->id === $post->user_id;
    }
}
// In controller
$this->authorize('update', $post);
```

### FastAPI

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

# Role-based access
async def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, user: User = Depends(require_admin)):
    pass
```

### Plotly Dash

```python
# Basic auth (simple, limited)
import dash_auth
auth = dash_auth.BasicAuth(app, {"user": "password"})  # Don't hardcode in production

# For production, use Dash Enterprise auth or wrap with Flask-Login
from flask_login import LoginManager, login_required, current_user

login_manager = LoginManager()
login_manager.init_app(app.server)

# Protect Flask routes
@app.server.route('/data')
@login_required
def get_data():
    pass

# In callbacks, check user identity
@app.callback(Output('content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if not current_user.is_authenticated:
        return html.Div("Please log in")
```

## Password Handling

**Never store plain passwords. Use framework-provided hashing.**

```php
// WordPress - automatic hashing
wp_set_password($new_password, $user_id);
$is_valid = wp_check_password($password, $hashed_password, $user_id);
```

```python
# Django - automatic hashing
user.set_password(raw_password)
user.save()
# Verification
from django.contrib.auth.hashers import check_password
check_password(raw_password, user.password)
```

```php
// Laravel - bcrypt by default
$hashed = Hash::make($password);
Hash::check($password, $hashed);
```

```python
# FastAPI/Dash - use passlib or werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
hashed = generate_password_hash(password)
check_password_hash(hashed, password)
```

## IDOR (Insecure Direct Object References)

Always verify the requesting user has access to the specific resource, not just the resource type:

```python
# WRONG - Any authenticated user can access any order
@app.get("/orders/{order_id}")
async def get_order(order_id: int, user: User = Depends(get_current_user)):
    return db.query(Order).get(order_id)

# RIGHT - Verify ownership
@app.get("/orders/{order_id}")
async def get_order(order_id: int, user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404)
    return order
```
