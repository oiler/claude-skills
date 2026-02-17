# Secure Data Handling

## PII (Personally Identifiable Information)

### Storage Rules

- Encrypt sensitive data at rest when the database or storage isn't encrypted at the volume level
- Never log PII (emails, passwords, SSNs, credit card numbers, phone numbers)
- Use hashed or tokenized references when the original value isn't needed
- Implement data retention policies — delete what you don't need
- Minimize data collection — only collect what's required

### Logging Safety

```php
// WordPress
error_log("User login: {$username}");     // OK — username is not secret
error_log("Password: {$password}");       // NEVER
error_log("Email: {$email}");             // AVOID — PII in logs

// Sanitize before logging
error_log("User action: " . sanitize_text_field($action));
```

```python
# Django / FastAPI / Dash
import logging
logger = logging.getLogger(__name__)

logger.info(f"User {user.id} logged in")            # OK — use IDs, not PII
logger.info(f"Password: {password}")                 # NEVER
logger.info(f"Processing order for {user.email}")    # AVOID
logger.info(f"Processing order for user {user.id}")  # BETTER
```

```python
# Django — Filter sensitive data from error reports
# settings.py
DEFAULT_EXCEPTION_REPORTER_FILTER = 'django.views.debug.SafeExceptionReporterFilter'
SENSITIVE_VARIABLES_RE = r'(?i)(password|secret|token|key|ssn|credit)'

# On specific views
from django.views.decorators.debug import sensitive_variables

@sensitive_variables('password', 'credit_card')
def process_payment(request):
    password = request.POST['password']  # Won't appear in error reports
```

### Data Minimization in Queries

```python
# Django — Only select needed columns
User.objects.only('id', 'username')  # Don't fetch email, phone, etc. unless needed
User.objects.defer('ssn', 'phone')   # Exclude sensitive columns

# In serializers, explicitly declare fields
class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name']  # No email, phone, etc.
```

## Payment and Credit Card Data

**Never store credit card data directly. Use payment processors.**

```python
# RIGHT — Use Stripe (or similar) tokens
import stripe

class Order(models.Model):
    stripe_payment_intent_id = models.CharField(max_length=255)
    last_four = models.CharField(max_length=4)  # Only last 4 digits, if needed
    # NEVER: credit_card_number, cvv, expiry_date
```

```php
// WordPress/WooCommerce — Let payment gateways handle sensitive data
update_post_meta($order_id, '_transaction_id', sanitize_text_field($transaction_id));
// NEVER store full card numbers or CVV
```

**PCI DSS compliance rules:**
- Never store CVV/CVC after authorization
- Never store full card numbers in plaintext
- Never log card data
- Use tokenization (Stripe, Braintree, PayPal) — the card data never touches your server

## Encryption

### Passwords

Always use framework-provided password hashing — never implement your own:

```python
# Django (uses PBKDF2 by default, configurable to Argon2)
user.set_password(raw_password)
# To use Argon2 (recommended):
# pip install argon2-cffi
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

```php
// WordPress — built-in
wp_hash_password($password);

// Laravel — bcrypt by default
Hash::make($password);
```

### Application-Level Encryption

For encrypting data at the application level (e.g., API keys stored in your database):

```python
# Python — Use Fernet (symmetric encryption)
from cryptography.fernet import Fernet

# Generate key once, store securely (NOT in code)
key = Fernet.generate_key()  # Store in env var or secrets manager

cipher = Fernet(key)
encrypted = cipher.encrypt(b"sensitive data")
decrypted = cipher.decrypt(encrypted)
```

```php
// Laravel — Built-in encryption
$encrypted = encrypt($sensitiveData);
$decrypted = decrypt($encrypted);
// Uses APP_KEY from .env (AES-256-CBC)
```

### Never Roll Your Own

```python
# WRONG — Homemade "encryption"
import base64
encoded = base64.b64encode(password.encode())  # This is encoding, NOT encryption
encrypted = ''.join(chr(ord(c) + 3) for c in data)  # Caesar cipher is not security

# WRONG — MD5/SHA for passwords
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # Trivially crackable
hashed = hashlib.sha256(password.encode()).hexdigest()  # Fast = bad for passwords
```
