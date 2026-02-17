# SQL Injection Prevention

## Core Rule

Never construct SQL queries by concatenating or interpolating user input. Always use parameterized queries, prepared statements, or the ORM.

## WordPress

**Use $wpdb->prepare():**
```php
global $wpdb;

// RIGHT - Prepared statement with typed placeholders
$results = $wpdb->get_results($wpdb->prepare(
    "SELECT * FROM {$wpdb->posts} WHERE post_author = %d AND post_status = %s",
    $user_id,
    $status
));

// RIGHT - INSERT/UPDATE
$wpdb->query($wpdb->prepare(
    "UPDATE {$wpdb->postmeta} SET meta_value = %s WHERE post_id = %d AND meta_key = %s",
    $new_value, $post_id, $meta_key
));
```

**Use WP_Query for post queries (safer high-level API):**
```php
$query = new WP_Query([
    'author' => $user_id,
    'post_status' => $status,
    'meta_query' => [
        ['key' => $meta_key, 'value' => $meta_value]
    ]
]);
```

**Anti-patterns:**
```php
// WRONG - Direct interpolation
$wpdb->query("SELECT * FROM {$wpdb->posts} WHERE ID = {$_GET['id']}");

// WRONG - esc_sql alone is not sufficient
$wpdb->query("SELECT * FROM posts WHERE title = '" . esc_sql($_POST['title']) . "'");
```

## Django

**ORM is safe by default:**
```python
# RIGHT - ORM parameterizes automatically
User.objects.filter(username=user_input)
Post.objects.filter(author_id=user_id, status=status)

# RIGHT - Q objects for complex queries
from django.db.models import Q
User.objects.filter(Q(username=search) | Q(email=search))
```

**Raw queries must use parameters:**
```python
# RIGHT - Parameterized
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE username = %s", [user_input])

# RIGHT - RawSQL with params
User.objects.raw("SELECT * FROM users WHERE username = %s", [user_input])

# WRONG - String formatting
cursor.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
```

**Extra/RawSQL expressions:**
```python
# RIGHT - Parameterized extra
queryset.extra(where=["username = %s"], params=[user_input])

# WRONG - Direct interpolation in extra
queryset.extra(where=[f"username = '{user_input}'"])
```

## Laravel

**Eloquent and Query Builder are safe:**
```php
// RIGHT - Query builder with bindings
DB::table('users')->where('email', $email)->where('status', $status)->get();

// RIGHT - Eloquent
User::where('email', $email)->first();
```

**Raw queries must use bindings:**
```php
// RIGHT - Named bindings
DB::select('SELECT * FROM users WHERE email = :email', ['email' => $email]);

// RIGHT - Positional bindings
DB::select('SELECT * FROM users WHERE email = ?', [$email]);

// CAUTION - whereRaw needs bindings too
DB::table('users')->whereRaw('email = ?', [$email])->get();

// WRONG - String concatenation
DB::select("SELECT * FROM users WHERE email = '{$email}'");
```

## FastAPI

**SQLAlchemy ORM is safe:**
```python
# RIGHT - ORM
session.query(User).filter(User.username == user_input).first()

# RIGHT - Text with parameters
from sqlalchemy import text
session.execute(text("SELECT * FROM users WHERE username = :username"), {"username": user_input})

# WRONG - String formatting
session.execute(text(f"SELECT * FROM users WHERE username = '{user_input}'"))
```

## Plotly Dash

Dash callbacks that query databases are a common injection vector because callback inputs can be spoofed:

```python
@app.callback(Output('table', 'data'), Input('search', 'value'))
def search(query):
    # WRONG - Untrusted callback input in SQL
    df = pd.read_sql(f"SELECT * FROM data WHERE name LIKE '%{query}%'", conn)

    # RIGHT - Parameterized query
    df = pd.read_sql("SELECT * FROM data WHERE name LIKE %s", conn, params=[f"%{query}%"])

    # RIGHT - SQLAlchemy with parameters
    from sqlalchemy import text
    result = conn.execute(text("SELECT * FROM data WHERE name LIKE :q"), {"q": f"%{query}%"})
    df = pd.DataFrame(result.fetchall())
```

## LIKE Clause Escaping

When using LIKE with user input, escape the wildcard characters too:

```python
# Python - Escape % and _ in LIKE patterns
import re
safe_input = re.sub(r'([%_])', r'\\\1', user_input)
cursor.execute("SELECT * FROM posts WHERE title LIKE %s", [f"%{safe_input}%"])
```

```php
// PHP/WordPress - Escape LIKE wildcards
$safe = $wpdb->esc_like($user_input);
$wpdb->prepare("SELECT * FROM {$wpdb->posts} WHERE post_title LIKE %s", "%{$safe}%");
```
