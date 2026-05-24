# Password Policy and Storage

Covers modern password rules per NIST SP 800-63B (rev 4, August 2024), breached-password checking, per-framework storage, and login-flow protections. Does not cover 2FA — see the pointer at the end.

## What Modern Password Policy Says

NIST SP 800-63B rev 4 (August 2024) is the authoritative source. The key rules:

| Rule | Requirement |
|---|---|
| Minimum length | 8 characters (memorized secrets); 15 recommended for user-chosen passwords |
| Maximum length | At least 64 characters — do not truncate |
| Character set | All printable ASCII + Unicode; allow spaces and paste |
| Complexity rules | **Prohibited** — no forced uppercase/digit/symbol mix |
| Periodic rotation | **Prohibited** — only rotate on evidence of compromise |
| Breached passwords | **Required** — check against known-breach lists at creation and reset |
| Hints / security questions | **Prohibited** |
| Hashing | Required — strong adaptive algorithm with per-user salt |

**Why NIST dropped complexity rules:** Forced complexity doesn't produce strong passwords — it produces predictable patterns. "Password1!" satisfies every rule and is trivially cracked. Length and breach-checking are far stronger signals of password quality. Users who can choose any 20-character passphrase consistently outperform users forced into "Tr0ub4dor&3" patterns.

**Why no rotation:** Mandatory rotation trains users to make predictable incremental changes ("Password1!" → "Password2!") and creates support burden with no measurable security gain. Rotate only when credentials are known or suspected compromised.

## Breached-Password Checking

Use the Have I Been Pwned (HIBP) k-anonymity API. The k-anonymity model ensures you never send the full password or full hash to a third party — only the first 5 characters of the SHA-1 hash are transmitted, and matching is done locally.

**The pattern:**
1. SHA-1 hash the plaintext password
2. Send the first 5 hex characters to `api.pwnedpasswords.com/range/{prefix}`
3. The API returns all suffixes matching that prefix with breach counts
4. Compare the remaining 35 characters locally — never leave your server

**Python (Django / FastAPI / Dash):**
```python
import hashlib
import httpx  # or requests

def is_password_pwned(password: str) -> bool:
    """Return True if the password appears in any known breach."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    # Only the 5-char prefix leaves the server
    response = httpx.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
    response.raise_for_status()

    for line in response.text.splitlines():
        candidate_suffix, count = line.split(":")
        if candidate_suffix == suffix:
            return True  # Found in breach list — reject the password
    return False

# Usage at registration / password reset:
if is_password_pwned(raw_password):
    raise ValidationError(
        "This password has appeared in a data breach. Choose a different one."
    )
```

**PHP (WordPress / Laravel):**
```php
function is_password_pwned(string $password): bool {
    $sha1   = strtoupper(sha1($password));
    $prefix = substr($sha1, 0, 5);
    $suffix = substr($sha1, 5);

    $url      = 'https://api.pwnedpasswords.com/range/' . $prefix;
    $response = wp_remote_get($url, ['timeout' => 5]); // WordPress
    // Laravel: Http::get($url)->body();

    if (is_wp_error($response)) {
        // Fail open — don't block registration if HIBP is unreachable
        return false;
    }

    $body  = wp_remote_retrieve_body($response);
    $lines = explode("\r\n", $body);

    foreach ($lines as $line) {
        [$candidate, $count] = explode(':', $line);
        if ($candidate === $suffix) {
            return true;
        }
    }
    return false;
}
```

**Fail-open vs fail-closed:** If the HIBP API is unreachable, failing open (allowing the registration) is the safer default for availability. Log the failure and alert — don't silently swallow it. Fail-closed only if your threat model demands it and you control the breach list locally.

## Storage — Per Framework

### WordPress

Use `wp_hash_password()` and `wp_check_password()`. WordPress uses phpass under the hood, which applies bcrypt-equivalent stretching with a per-user salt.

```php
// Hashing (registration / password reset)
$hash = wp_hash_password($plaintext_password);

// Verification (login)
if (wp_check_password($submitted_password, $stored_hash, $user->ID)) {
    // authenticated
}
```

```php
// WRONG — never store raw or weakly-hashed passwords
$hash = md5($password);       // WRONG
$hash = sha1($password);      // WRONG
$hash = hash('sha256', $password); // WRONG — fast hashes are not password hashes
update_user_meta($user_id, 'password', $password); // WRONG — plaintext
```

WordPress automatically rehashes legacy phpass hashes to bcrypt on next login when running PHP 7.4+ and WordPress 5.5+. Don't bypass this by rolling your own.

### Laravel

`Hash::make()` defaults to bcrypt (cost 10). Upgrade to Argon2id for stronger resistance against GPU attacks:

```php
// Default — bcrypt
$hash = Hash::make($password);
$valid = Hash::check($submitted, $stored_hash);
```

```php
// config/hashing.php — switch to argon2id
'driver' => 'argon2id',

'argon' => [
    'memory' => 65536,   // 64 MB
    'threads' => 1,
    'time'    => 4,
],
```

```php
// WRONG
$hash = md5($password);                  // WRONG
$hash = openssl_encrypt($password, ...); // WRONG — encryption is reversible
```

Laravel's `Hash::needsRehash()` detects outdated bcrypt hashes on login, letting you transparently rehash when the user authenticates.

### Django

Django defaults to PBKDF2-SHA256 with 600,000 iterations (Django 4.2+). Upgrade to Argon2id for stronger GPU resistance:

```python
# settings.py — add argon2 at the top; Django tries hashers in order
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # new passwords
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # legacy — verified + rehashed
]
```

```python
# pip install argon2-cffi — then use transparently via the auth system
from django.contrib.auth.hashers import make_password, check_password

hashed = make_password(raw_password)
is_valid = check_password(submitted, hashed)
```

```python
# WRONG
import hashlib
stored = hashlib.sha256(password.encode()).hexdigest()  # WRONG — no salt, no stretching

# WRONG — storing in a non-password field without hashing
user.notes = password  # WRONG — plaintext
```

Django auto-rehashes PBKDF2 hashes to Argon2 on next login once Argon2 is at the top of `PASSWORD_HASHERS`.

### FastAPI

FastAPI has no built-in password hashing. Use `passlib` with Argon2id:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plaintext: str) -> str:
    return pwd_context.hash(plaintext)

def verify_password(plaintext: str, hashed: str) -> bool:
    return pwd_context.verify(plaintext, hashed)
    # verify() uses constant-time comparison internally — never use ==
```

```bash
pip install "passlib[argon2]"
```

```python
# WRONG
import hashlib
stored = hashlib.sha256(password.encode()).hexdigest()  # WRONG
if password == stored_password:  # WRONG — plaintext comparison leaks timing info
    ...
```

### Plotly Dash

Dash apps typically authenticate through Flask-Login or an upstream auth layer (Okta, Auth0, corporate SSO). When you do own the credential store, the passlib pattern above is the right default — Dash runs on Flask, so import and call it the same way as FastAPI.

If you're using `dash-auth` for simple HTTP Basic Auth on internal tools, be aware it stores credentials in plaintext in your code. Replace it with Flask-Login + passlib for anything beyond a demo.

## Login Flow Protections

### Constant-time comparison

Never compare password hashes with `==`. Hash comparison must be constant-time to prevent timing attacks that leak whether the hash prefix matched.

```python
# WRONG — timing leaks
if stored_hash == compute_hash(submitted):
    ...

# RIGHT — use the library's verify function
pwd_context.verify(submitted, stored_hash)     # passlib
check_password(submitted, stored_hash)          # Django
```

```php
// RIGHT — PHP has a dedicated function
if (password_verify($submitted, $stored_hash)) { ... }

// For token comparison (CSRF, API keys)
if (hash_equals($expected, $submitted)) { ... }
```

### Rate limiting

Apply rate limits at two dimensions — per username and per IP — to cover both targeted attacks (attacker knows the username) and distributed attacks (attacker rotates usernames). See `api-security.md` for per-framework rate-limit patterns.

Thresholds for login endpoints are tighter than general API limits: 5–10 attempts per username per 15 minutes is a reasonable starting point.

### Generic error messages

Don't tell an attacker whether the username exists:

```python
# WRONG — confirms username exists
if not user:
    return "No account with that email."
if not verify_password(submitted, user.password_hash):
    return "Wrong password."

# RIGHT — same message either way
return "Invalid email or password."
```

The same rule applies to password reset: "If that email exists, we sent a reset link" — not "We sent you a reset link" (which confirms the account).

### Account lockout vs. throttling

Hard lockout (block after N failures) is vulnerable to DoS: an attacker who knows your usernames can lock out every user. Prefer exponential backoff — slow the response time geometrically after each failure, return HTTP 429, and add a CAPTCHA threshold. Reserve hard lockout for high-value accounts where DoS is an acceptable tradeoff.

## What NOT to Do

Explicit list of dead patterns — each one is actively harmful:

- **md5 / sha1 / sha256 alone** for password storage — these are fast by design; an attacker with your database can test billions of guesses per second
- **Salted sha256** — still a fast hash; salting prevents rainbow tables but doesn't prevent brute-force at scale
- **Composition rules** — uppercase + digit + symbol requirements produce predictable user behavior, not strong passwords
- **Periodic rotation** — no security benefit; creates support burden and encourages weak incremental changes
- **Password hints** — leak credential structure; prohibited by NIST 800-63B
- **Reversible encryption** for passwords — if the key is compromised, every password is compromised; use one-way hashing
- **Disabling paste** in password fields — breaks password managers, which are your best ally for producing strong, unique passwords
- **Truncating passwords** at short lengths (e.g., 20 or 32 chars) — silently breaks long passphrases; maximum must be at least 64
- **Sending passwords in cleartext over email** — at registration, at reset, or ever; send a single-use reset link instead
- **Logging submitted passwords** — even in debug mode; they end up in log aggregators and are hard to purge

## 2FA / MFA

2FA implementation is out of scope for this reference. The short answer: prefer TOTP (RFC 6238) with WebAuthn/passkeys as the upgrade path; avoid SMS OTP for new systems (SIM-swapping and SS7 attacks make it the weakest MFA option still in common use). A future reference will cover TOTP setup, backup codes, and WebAuthn per framework.
