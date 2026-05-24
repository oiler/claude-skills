# Path Traversal Prevention

Untrusted input used to construct a file path can escape its intended base directory via `../` sequences, absolute paths, URL-encoded variants (`%2e%2e%2f`), null bytes (`%00`), or symlinks that point outside the base. The result is unauthorized read, write, or include of arbitrary files.

## The Canonical Defense Pattern

Regardless of framework or language:

1. Resolve the user-supplied path to its **absolute canonical form** — expanding `..`, symlinks, and encoded characters.
2. Verify the resolved path **starts with the intended base directory**.
3. Reject any path that does not.

Never try to strip or block `..` sequences before opening — normalization must happen at the OS level via `realpath`/`resolve`, not by string manipulation.

## Python (Django, FastAPI, Dash)

### pathlib — preferred (Python 3.9+)

```python
from pathlib import Path

BASE_DIR = Path("/var/app/uploads").resolve()

def safe_open(user_filename: str) -> Path:
    # resolve() expands symlinks and normalizes ../
    target = (BASE_DIR / user_filename).resolve()

    # is_relative_to() checks that target is inside BASE_DIR
    if not target.is_relative_to(BASE_DIR):
        raise PermissionError(f"Access denied: {user_filename!r}")

    return target
```

`Path.resolve()` calls the OS — it handles `../`, absolute overrides, symlinks, and URL-decoded sequences that reached this point already decoded.

### Older idiom (Python 3.8 and below)

```python
import os

BASE_DIR = os.path.realpath("/var/app/uploads")

def safe_open(user_filename: str) -> str:
    target = os.path.realpath(os.path.join(BASE_DIR, user_filename))

    # Trailing separator prevents a prefix match on a sibling directory
    # e.g. /var/app/uploads-extra would match "/var/app/uploads" without it
    if not target.startswith(BASE_DIR + os.sep):
        raise PermissionError(f"Access denied: {user_filename!r}")

    return target
```

### Django — file serving from a model or view

```python
from pathlib import Path
from django.http import FileResponse, Http404
from django.conf import settings

MEDIA_ROOT = Path(settings.MEDIA_ROOT).resolve()

def serve_upload(request, filename):
    target = (MEDIA_ROOT / filename).resolve()

    if not target.is_relative_to(MEDIA_ROOT):
        raise Http404

    if not target.is_file():
        raise Http404

    return FileResponse(target.open("rb"))
```

```python
# WRONG - resolve() called after open; by then you've already opened the file
with open(os.path.join(BASE_DIR, user_filename)) as f:  # traversal succeeds here
    content = f.read()

# WRONG - basename() alone does not prevent absolute paths on all platforms
# and strips directory context the caller may have intended
safe = os.path.basename(user_filename)  # "/etc/passwd" → "passwd", but that's a coincidence
```

### FastAPI — FileResponse

```python
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()
STATIC_DIR = Path("/var/app/static").resolve()

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    target = (STATIC_DIR / file_path).resolve()

    if not target.is_relative_to(STATIC_DIR):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.is_file():
        raise HTTPException(status_code=404)

    return FileResponse(target)
```

```python
# WRONG - passing user input directly to FileResponse
@app.get("/files/{name}")
async def get_file(name: str):
    return FileResponse(f"/var/app/static/{name}")  # ../../../etc/passwd works here
```

### Plotly Dash — send_file / open in callbacks

Dash callback inputs are fully untrusted — a user can POST arbitrary values regardless of what the UI shows.

```python
from pathlib import Path
from flask import send_file
import dash

UPLOAD_DIR = Path("/var/app/uploads").resolve()

@app.callback(Output("download", "data"), Input("filename-store", "data"))
def serve_file(filename):
    if not filename:
        raise dash.exceptions.PreventUpdate

    target = (UPLOAD_DIR / filename).resolve()

    if not target.is_relative_to(UPLOAD_DIR) or not target.is_file():
        raise dash.exceptions.PreventUpdate  # or return an error component

    # Use send_file with the resolved absolute path
    return dcc.send_file(str(target))
```

## PHP (WordPress + Laravel)

### Core PHP pattern

```php
// RIGHT
$base = realpath('/var/app/uploads');
$target = realpath($base . '/' . $user_filename);

// realpath() returns false if the path does not exist — treat false as a rejection
if ($target === false || !str_starts_with($target, $base . DIRECTORY_SEPARATOR)) {
    http_response_code(403);
    exit('Access denied');
}

readfile($target);
```

`realpath()` returns the canonical absolute path with symlinks resolved, or `false` for non-existent paths. The `false` return is itself a security signal — a traversal target that doesn't exist yet still fails safely.

```php
// WRONG - string manipulation instead of OS-level normalization
$filename = str_replace('../', '', $user_filename);  // ....// bypasses this
$path = '/var/app/uploads/' . $filename;
readfile($path);

// WRONG - normalizing after accessing
include '/var/app/uploads/' . $user_filename;  // too late
```

### WordPress

```php
// RIGHT - resolve and verify against ABSPATH or a custom uploads dir
$upload_dir = wp_get_upload_dir();
$base = realpath($upload_dir['basedir']);
$target = realpath($base . '/' . sanitize_file_name($user_filename));

if ($target === false || !str_starts_with($target, $base . DIRECTORY_SEPARATOR)) {
    wp_die('Access denied', 403);
}

readfile($target);
```

`sanitize_file_name()` removes characters illegal in filenames and strips dangerous sequences, but it does **not** prevent path traversal on its own — it does not expand `../` or resolve symlinks. Always follow it with the `realpath()` + prefix check.

`wp_normalize_path()` converts backslashes to forward slashes for consistent string handling on Windows hosts. Use it before `realpath()` when you want consistent separators, but it does not substitute for `realpath()`.

The classic plugin/theme include vulnerability:

```php
// WRONG - directly including a user-supplied page parameter
$page = $_GET['page'];
include_once ABSPATH . 'wp-content/plugins/myplugin/pages/' . $page . '.php';
// Attack: ?page=../../../../wp-config

// RIGHT - allowlist the permitted page names
$allowed_pages = ['dashboard', 'settings', 'reports'];
$page = $_GET['page'] ?? '';
if (!in_array($page, $allowed_pages, true)) {
    wp_die('Invalid page', 403);
}
include_once ABSPATH . 'wp-content/plugins/myplugin/pages/' . $page . '.php';
```

Allowlisting is the strongest defense for include paths — it eliminates the traversal surface entirely rather than trying to sanitize it.

### Laravel

```php
// RIGHT - Storage facade enforces disk root automatically
use Illuminate\Support\Facades\Storage;

// Files are constrained to the disk root defined in config/filesystems.php
$contents = Storage::disk('local')->get($user_filename);

// For serving downloads
return Storage::disk('local')->download($user_filename);
```

The `Storage` facade's disk root is the canonical base — Laravel's Flysystem layer resolves paths relative to that root. Prefer this over manual `realpath()` checks when the file is already on a managed disk.

When you must construct paths manually:

```php
use Illuminate\Support\Str;

$base = realpath(storage_path('app/uploads'));
$target = realpath($base . '/' . $user_filename);

if ($target === false || !Str::startsWith($target, $base . DIRECTORY_SEPARATOR)) {
    abort(403);
}

return response()->file($target);
```

```php
// WRONG - trusting the path without resolution
$path = storage_path('app/uploads/' . $request->input('file'));
return response()->file($path);  // ../../../.env serves the env file
```

## File Upload Destinations

This section covers the read/serve side. For the upload side — validating MIME types, restricting extensions, preventing executable uploads — see `file-upload-security.md`.

One rule applies to both sides: filenames extracted from uploaded archives (zip, tar) or from `Content-Disposition` headers must be sanitized before being used as paths. Apply the same resolve + verify-inside-base check to any filename you did not generate yourself.

## Storage location is a separate concern from traversal defense

Containing user-controlled paths inside an allowed base directory prevents *traversal*. It does not prevent *exposure*. If the base directory itself is under the web root (e.g., `/var/www/uploads/`), every successfully-uploaded file is reachable by URL — including ones an authenticated user uploaded for private review, ones containing PII, and ones whose existence is itself sensitive. Worse, if the upload directory permits server-side execution (PHP, CGI), an attacker who uploads a `.php` file with a benign extension trick can get RCE even with a perfect traversal defense.

**Store user uploads outside the web root.** Serve them through a framework view that checks authorization, sets the correct `Content-Disposition`, and refuses to execute. Example bases: `/var/app-data/uploads/` (not under any web-server vhost root), `~/.local/share/myapp/uploads/`, or an object store like S3 with private ACLs. The traversal defense above still applies — but it's defense in depth, not the only defense.

## Anti-Patterns

- **Blocklisting `../`** — attackers bypass with `....//`, URL encoding (`%2e%2e%2f`), or double encoding (`%252e%252e%252f`). OS-level resolution defeats all variants at once.
- **Trusting `basename()`** — `basename('/etc/passwd')` returns `passwd`, which looks safe, but this strips context and can still land outside your base if the base itself is wrong. It also does nothing for symlinks.
- **Normalizing after opening** — checking the path after `fopen`, `include`, or `readfile` is too late; the syscall already ran.
- **Relying on the web server's document root** — a script that opens files with an absolute path bypasses document-root restrictions entirely.
- **Forgetting that `realpath()` / `resolve()` require the path to exist** — if the file must not yet exist (e.g., an upload destination), verify the **parent directory** is inside the base, not the full target path.
