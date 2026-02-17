# Environment and Configuration Security

## Secrets Management

### Never Hardcode Secrets

```python
# WRONG
SECRET_KEY = "django-insecure-abc123"
DATABASE_URL = "postgres://user:password@localhost/db"
API_KEY = "sk_live_123456789"

# RIGHT — Environment variables
import os
SECRET_KEY = os.environ['SECRET_KEY']
DATABASE_URL = os.environ['DATABASE_URL']
```

### Use .env Files for Local Development

```bash
# .env (MUST be in .gitignore)
SECRET_KEY=your-random-secret-key-here
DB_PASSWORD=localdevpassword
API_KEY=sk_test_123
DEBUG=True
```

**Django:**
```python
# pip install python-decouple
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
DATABASE_URL = config('DATABASE_URL')
```

**Laravel:**
```php
// .env file is used by default
// Access via env() helper
'key' => env('APP_KEY'),
'debug' => env('APP_DEBUG', false),
```

**WordPress:**
```php
// wp-config.php
define('DB_PASSWORD', getenv('DB_PASSWORD'));
define('AUTH_KEY', getenv('AUTH_KEY'));
// Generate salts: https://api.wordpress.org/secret-key/1.1/salt/
```

**FastAPI/Dash:**
```python
# pip install pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    database_url: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### .gitignore Essentials

```gitignore
# Environment files
.env
.env.local
.env.production

# IDE and OS
.idea/
.vscode/
.DS_Store

# Sensitive configs
wp-config.php  # If using env vars, this might be safe to commit
*.pem
*.key
```

### Production Secrets

For production, use a secrets manager instead of .env files:
- AWS Secrets Manager / Systems Manager Parameter Store
- Google Cloud Secret Manager
- HashiCorp Vault
- Azure Key Vault

## Debug Mode

**Always disable in production. Debug mode leaks stack traces, configuration, environment variables, and source code.**

**Django:**
```python
# settings.py (or separate production settings file)
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Debug toolbar — only in development
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
```

**WordPress:**
```php
// wp-config.php in production
define('WP_DEBUG', false);
define('WP_DEBUG_DISPLAY', false);
define('WP_DEBUG_LOG', false);
define('SCRIPT_DEBUG', false);
```

**Laravel:**
```php
// .env in production
APP_DEBUG=false
APP_ENV=production
```

**FastAPI:**
```python
# Never in production
app = FastAPI(debug=False)  # No auto-reload, no detailed errors

# Don't expose docs in production if API is internal
if not settings.debug:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
```

**Plotly Dash:**
```python
# WRONG in production
app.run(debug=True)  # Enables hot reload, exposes debugger with code execution

# RIGHT in production
app.run(debug=False)

# Also set Flask debug off
app.server.config['DEBUG'] = False
```

## Error Handling

### Production Error Messages

```python
# Django settings.py
DEBUG = False

# Custom error views
# urls.py
handler404 = 'myapp.views.custom_404'
handler500 = 'myapp.views.custom_500'

# views.py
def custom_500(request):
    return render(request, '500.html', status=500)
    # 500.html shows "Something went wrong" — no stack trace
```

```php
// Laravel — config/app.php
'debug' => false,

// Custom error pages in resources/views/errors/
// 404.blade.php, 500.blade.php, etc.
```

### Logging for Security

**What to log:**
- Authentication events (login success, login failure, logout)
- Authorization failures (access denied)
- Input validation failures
- System errors and exceptions
- Administrative actions (user creation, permission changes)

**What NOT to log:**
- Passwords (even failed attempts — log the username, not the password)
- Credit card numbers, SSNs, or other PII
- Session tokens or API keys
- Full request bodies containing sensitive data

```python
# Django — Configure structured logging
LOGGING = {
    'version': 1,
    'handlers': {
        'security': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/app/security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security'],
            'level': 'INFO',
        },
    },
}

# In code
security_logger = logging.getLogger('security')
security_logger.info(f"Login success: user_id={user.id} ip={request.META['REMOTE_ADDR']}")
security_logger.warning(f"Login failed: username={username} ip={request.META['REMOTE_ADDR']}")
# Note: log username for failed logins (to detect brute force), but NEVER log the password
```

## Dependency Management

Keep frameworks and packages updated. Known vulnerabilities in dependencies are a top attack vector.

```bash
# Python
pip audit                      # Check for known vulnerabilities
pip list --outdated            # See what needs updating
pip install --upgrade package  # Update specific package

# PHP (Composer)
composer audit                 # Check for vulnerabilities
composer outdated              # See updates available
composer update                # Update within constraints

# Node.js
npm audit                      # Check for vulnerabilities
npm audit fix                  # Auto-fix where possible
npm outdated                   # See updates

# Use lock files and commit them
# Python: requirements.txt or poetry.lock
# PHP: composer.lock
# Node: package-lock.json or yarn.lock
```

**Automate with Dependabot, Renovate, or Snyk** to get pull requests for dependency updates.
