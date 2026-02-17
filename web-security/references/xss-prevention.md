# XSS (Cross-Site Scripting) Prevention

## XSS Types

- **Stored XSS**: Malicious script saved in database, executes when retrieved and rendered
- **Reflected XSS**: Script in URL parameters reflected back in response
- **DOM-based XSS**: Client-side script manipulation without server involvement

## WordPress

**Escape output based on context:**
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

**Sanitize input on save:**
```php
$clean_text = sanitize_text_field($_POST['text']);
$clean_email = sanitize_email($_POST['email']);
$clean_url = esc_url_raw($_POST['url']);
$clean_html = wp_kses_post($_POST['content']); // Allow safe HTML subset
```

**Anti-patterns:**
```php
// WRONG - Direct output without escaping
echo $_POST['user_input'];
echo $wpdb->get_var("SELECT meta_value FROM ...");
```

## Django

**Template auto-escaping is enabled by default:**
```django
{# Automatically escaped #}
{{ user_input }}

{# Mark as safe ONLY if you have sanitized it yourself #}
{{ trusted_html|safe }}

{# JavaScript context #}
<script>var data = "{{ user_input|escapejs }}";</script>

{# JSON data in templates #}
{{ user_data|json_script:"data-id" }}
```

**Python code:**
```python
from django.utils.html import escape, format_html

safe_output = escape(user_input)
html = format_html('<a href="{}">{}</a>', url, text)  # auto-escapes both args
```

**Anti-patterns:**
```python
# WRONG - Marking untrusted content as safe
return mark_safe(request.POST['content'])

# WRONG - Disabling auto-escaping
{% autoescape off %}{{ user_content }}{% endautoescape %}
```

## Laravel

**Blade templates auto-escape:**
```php
{{-- Escaped (default, use this) --}}
{{ $user_input }}

{{-- Unescaped (use with extreme caution on pre-sanitized data only) --}}
{!! $trusted_html !!}

{{-- JavaScript context --}}
<script>var data = @json($user_data);</script>
```

**PHP escaping:**
```php
e($user_input); // htmlspecialchars wrapper
htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');
```

## FastAPI

**Jinja2 templates auto-escape:**
```html
{# Escaped by default #}
{{ user_input }}

{# Safe only if you have sanitized it #}
{{ trusted_html|safe }}
```

**Python code:**
```python
from markupsafe import escape
safe_output = escape(user_input)
```

## Plotly Dash

Dash avoids most XSS by design — components render via React, not raw HTML. Key risks:

```python
# WRONG - dangerously_set_inner_html with untrusted data
html.Div(dangerously_set_inner_html=user_input)

# RIGHT - Use Dash components which auto-escape
html.Div(children=user_input)  # Rendered as text, not HTML

# WRONG - Using dcc.Markdown with allow_dangerous_html=True and untrusted data
dcc.Markdown(user_input, dangerously_allow_html=True)

# RIGHT - Markdown without HTML rendering
dcc.Markdown(user_input)
```

**Callback inputs are untrusted** — a malicious user can craft HTTP requests with arbitrary callback inputs regardless of what your UI components allow:
```python
@app.callback(Output('output', 'children'), Input('dropdown', 'value'))
def update(value):
    # value can be ANYTHING, not just dropdown options
    # Validate before using
    if value not in ALLOWED_VALUES:
        raise PreventUpdate
```

## JavaScript (All Frameworks)

```javascript
// WRONG - innerHTML with user input
element.innerHTML = userInput;

// RIGHT - Safe text insertion
element.textContent = userInput;

// RIGHT - Sanitize HTML if you must render it
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);

// WRONG - eval-like patterns
element.onclick = new Function(userInput);
setTimeout(userInput, 1000);

// RIGHT - Event listeners
element.addEventListener('click', handler);
```
