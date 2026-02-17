# File Upload Security

## Validation Requirements

Always validate on the server side, even if you validate on the client:

1. **File extension** — allowlist only (never blocklist)
2. **MIME type** — check server-side with file content inspection, not just the client-supplied header
3. **File size** — enforce limits
4. **File name** — sanitize and rename
5. **File content** — validate that content matches claimed type

## WordPress

```php
// Use wp_handle_upload with strict type checking
$allowed_types = ['jpg|jpeg' => 'image/jpeg', 'png' => 'image/png', 'pdf' => 'application/pdf'];

$upload = wp_handle_upload($_FILES['file'], [
    'test_form' => false,
    'mimes' => $allowed_types
]);

if (isset($upload['error'])) {
    wp_die($upload['error']);
}

// Sanitize filename
$safe_filename = sanitize_file_name($_FILES['file']['name']);

// Verify MIME type server-side (don't trust $_FILES['type'])
$file_info = wp_check_filetype_and_ext($_FILES['file']['tmp_name'], $safe_filename);
if (!$file_info['type']) {
    wp_die('Invalid file type');
}
```

**Anti-pattern:**
```php
// WRONG - Trusting client-supplied MIME type
if ($_FILES['file']['type'] === 'image/jpeg') { /* This can be spoofed */ }
```

## Django

```python
from django.core.validators import FileExtensionValidator
import magic  # python-magic for content-based MIME detection

class DocumentForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])],
    )

def handle_upload(request):
    form = DocumentForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded = form.cleaned_data['file']

        # Enforce size limit
        if uploaded.size > 5 * 1024 * 1024:  # 5MB
            return HttpResponseBadRequest('File too large')

        # Verify MIME type with content inspection
        mime = magic.from_buffer(uploaded.read(2048), mime=True)
        uploaded.seek(0)
        if mime not in ['image/jpeg', 'image/png', 'application/pdf']:
            return HttpResponseBadRequest('Invalid file type')

        # Save with random filename to prevent path traversal
        import uuid
        ext = uploaded.name.rsplit('.', 1)[-1].lower()
        filename = f'uploads/{uuid.uuid4()}.{ext}'
        default_storage.save(filename, uploaded)
```

Also set in `settings.py`:
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
```

## Laravel

```php
// Validate in request
$request->validate([
    'file' => 'required|file|mimes:jpeg,png,pdf|max:5120'  // 5MB
]);

// Store with random name in private disk
$path = $request->file('file')->store('uploads', 'private');

// Or explicit random name
$safe_path = Storage::putFileAs(
    'uploads',
    $request->file('file'),
    Str::random(40) . '.' . $request->file('file')->extension()
);

// Serve private files through controller (not directly)
public function download($id) {
    $file = File::findOrFail($id);
    $this->authorize('download', $file);
    return Storage::disk('private')->download($file->path);
}
```

## FastAPI

```python
from fastapi import UploadFile, HTTPException
import uuid, magic

ALLOWED_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}
MAX_SIZE = 5 * 1024 * 1024  # 5MB

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Check size
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(413, "File too large")

    # Check MIME type from content (not from client)
    mime = magic.from_buffer(contents[:2048], mime=True)
    if mime not in ALLOWED_TYPES:
        raise HTTPException(400, "Invalid file type")

    # Save with random name
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ('jpg', 'jpeg', 'png', 'pdf'):
        raise HTTPException(400, "Invalid extension")
    safe_name = f"{uuid.uuid4()}.{ext}"
    with open(f"/secure/uploads/{safe_name}", "wb") as f:
        f.write(contents)
```

## Plotly Dash

```python
# dcc.Upload component returns base64-encoded content
@app.callback(Output('output', 'children'),
              Input('upload', 'contents'),
              State('upload', 'filename'))
def process_upload(contents, filename):
    if contents is None:
        raise PreventUpdate

    # Validate filename
    from werkzeug.utils import secure_filename
    safe_name = secure_filename(filename)
    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
    if ext not in ('csv', 'xlsx', 'json'):
        return html.Div("Invalid file type")

    # Decode and validate size
    import base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if len(decoded) > 10 * 1024 * 1024:  # 10MB
        return html.Div("File too large")

    # Process (e.g., read as DataFrame)
    import io, pandas as pd
    if ext == 'csv':
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
```

## General Rules

- **Rename uploaded files** — never use the original filename for storage
- **Store outside web root** — uploaded files should not be directly URL-accessible unless intentionally public
- **Serve through application** — use a controller/view to check permissions before serving
- **Scan for malware** — use ClamAV or similar in production
- **Watch for double extensions** — `file.php.jpg` may execute as PHP on misconfigured servers
- **Block null bytes** — `file.php%00.jpg` can truncate filenames on some systems
- **Limit upload frequency** — rate-limit upload endpoints to prevent abuse
