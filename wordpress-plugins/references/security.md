# WordPress Plugin Security

WordPress-specific security APIs and patterns. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025).

> **General OWASP fundamentals — XSS, CSRF, SQL injection theory, security headers, rate limiting — live in the `web-security` skill. This file covers only the WordPress-specific APIs that implement those defenses.**

---

## Nonces — CSRF Protection for Forms and AJAX

Nonces are single-use time-limited tokens that verify a request originated from your UI. They are **CSRF protection, not authorization** — always pair with a capability check.

### Forms

```php
// Output a hidden nonce field inside your <form> tag.
// $action must be a unique string identifying the operation.
wp_nonce_field( 'my_plugin_save_settings', 'my_plugin_nonce' );
```

### Admin form submission (POST handler)

```php
// check_admin_referer() verifies the nonce AND that the HTTP referrer originated from the WP admin area (CSRF defense, not authorization — still requires a current_user_can() check).
// Calls wp_die() automatically on failure — no manual die() needed.
add_action( 'admin_post_my_plugin_save', function (): void {
    check_admin_referer( 'my_plugin_save_settings', 'my_plugin_nonce' );
    current_user_can( 'manage_options' ) || wp_die( 'Unauthorized', '', [ 'response' => 403 ] );

    // Safe to process $_POST here.
} );
```

### AJAX handlers

```php
// Enqueue the nonce to JS via wp_localize_script().
wp_localize_script( 'my-plugin-js', 'myPlugin', [
    'nonce' => wp_create_nonce( 'my_plugin_ajax' ),
] );

// Server-side: check_ajax_referer() verifies the nonce; $die = true halts on failure.
add_action( 'wp_ajax_my_plugin_action', function (): void {
    check_ajax_referer( 'my_plugin_ajax', 'nonce' );
    current_user_can( 'edit_posts' ) || wp_send_json_error( 'Unauthorized', 403 );

    // Process and respond.
    wp_send_json_success( [ 'ok' => true ] );
} );
```

### Manual nonce verify (non-form flows)

`wp_verify_nonce( $nonce, $action )` returns `false` on failure, `1` if the token is ≤12 hours old, `2` if it is 12–24 hours old.

```php
if ( ! wp_verify_nonce( $_POST['nonce'] ?? '', 'my_plugin_action' ) ) {
    wp_die( 'Nonce check failed.', '', [ 'response' => 403 ] );
}
```

---

## Capability Checks — Authorization

Check capabilities, not role names. Role names are UI labels that can be renamed or reassigned; capabilities are the stable security contract.

```php
if ( ! current_user_can( 'manage_options' ) ) {
    wp_die( 'You do not have permission to do this.', '', [ 'response' => 403 ] );
}
```

### Per-object capabilities

Pass the object ID as the third argument; `map_meta_cap()` resolves ownership, post status, and custom post type caps automatically.

```php
if ( ! current_user_can( 'edit_post', $post_id ) ) {
    wp_die( 'You cannot edit this post.', '', [ 'response' => 403 ] );
}
```

Common capabilities: `manage_options` (settings), `edit_posts` (post editing), `upload_files` (media), `edit_post` + `$post_id` (per-object). Never check `is_admin()` as an authorization gate — it tests the request path, not the user's role.

---

## Escape at Output (Late Escaping)

Escape **at the echo site**, not on input or storage. The correct escape function depends on the output context (HTML body, attribute, URL, JS), which is only known at render time.

```php
echo esc_html( $user_input );                              // HTML body text — entity-encodes < > & " ' (does NOT strip tags)
echo '<input value="' . esc_attr( $user_input ) . '">';   // attribute value
echo '<a href="' . esc_url( $url ) . '">';                 // href/src — safe schemes only
echo '<script>var x = "' . esc_js( $v ) . '";</script>';  // JS string literal
echo '<textarea>' . esc_textarea( $content ) . '</textarea>'; // preserves newlines

echo wp_kses_post( $html_content );  // allowed post HTML — strips disallowed tags

// Custom allowlist when wp_kses_post is too broad.
echo wp_kses( $html_content, [
    'a'      => [ 'href' => [], 'title' => [] ],
    'strong' => [],
    'em'     => [],
] );
```

### Translations

Use the escape+i18n combo helpers so translated strings are never echoed raw:

```php
esc_html_e( 'Settings saved.', 'my-plugin' );   // echo
esc_attr_e( 'Enter a value', 'my-plugin' );      // echo in attribute
$label = esc_html__( 'Settings saved.', 'my-plugin' ); // return
```

---

## Sanitize on Input

Sanitize all external input before using it in logic or storage. Use the most specific sanitizer for the expected value type.

```php
// Arbitrary user-facing text — strips tags, trims whitespace.
$title = sanitize_text_field( wp_unslash( $_POST['title'] ?? '' ) );

// Multi-line text.
$body = sanitize_textarea_field( wp_unslash( $_POST['body'] ?? '' ) );

// Positive integers (IDs, counts).
$post_id = absint( $_POST['post_id'] ?? 0 );

// Any integer (including negative).
$offset = intval( $_POST['offset'] ?? 0 );

// Option/meta keys — only lowercase alphanumeric, dashes, underscores.
$key = sanitize_key( $_POST['key'] ?? '' );

// Email addresses.
$email = sanitize_email( $_POST['email'] ?? '' );

// URLs for storage (esc_url_raw, not esc_url — esc_url adds display encoding).
$url = esc_url_raw( wp_unslash( $_POST['url'] ?? '' ) );

// File names.
$filename = sanitize_file_name( $_FILES['upload']['name'] ?? '' );
```

### `wp_unslash()` before sanitizing

WordPress magic-quotes all superglobals (`$_POST`, `$_GET`, `$_COOKIE`, `$_REQUEST`). Always call `wp_unslash()` before any sanitization function, otherwise slashes appear in the sanitized output (as shown in every example above).

### Validate against allowlists

When the input must be one of a known set of values (e.g. a post status, a tab name), validate after sanitizing:

```php
$allowed_tabs = [ 'general', 'advanced', 'tools' ];
$tab = sanitize_key( wp_unslash( $_GET['tab'] ?? 'general' ) );
if ( ! in_array( $tab, $allowed_tabs, true ) ) {
    $tab = 'general'; // Fall back to default; never trust unsanitized input.
}
```

---

## Prepared Statements (`$wpdb`)

Never interpolate user input into SQL. Always use `$wpdb->prepare()` with typed placeholders: `%d` (int), `%s` (string), `%f` (float).

```php
global $wpdb;

$results = $wpdb->get_results(
    $wpdb->prepare(
        "SELECT * FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key = %s",
        $post_id,
        $meta_key
    )
);
```

### `%i` — identifier placeholder (WP 6.2+)

Dynamic table or column names must use `%i`; do not use `%s` for identifiers.

```php
$rows = $wpdb->get_results(
    $wpdb->prepare(
        "SELECT * FROM %i WHERE status = %s",
        $wpdb->posts,  // table name
        'publish'
    )
);
```

Prefer core API functions (`WP_Query`, `get_post_meta`, `update_post_meta`, etc.) over raw SQL — they handle escaping internally. Use `$wpdb` only when no core API covers the query. For VIPCS rules around `$wpdb` and restricted direct-DB patterns, see [`vip-standards.md`](vip-standards.md).

---

## REST API — `register_rest_route`

Every route that writes or returns private data must have a real `permission_callback`. A missing callback triggers a `_doing_it_wrong()` notice in WP 5.5+. Never use `__return_true` for anything that changes state or exposes private data.

```php
register_rest_route( 'my-plugin/v1', '/settings', [
    'methods'             => WP_REST_Server::EDITABLE, // PUT + PATCH
    'callback'            => 'my_plugin_update_settings',
    'permission_callback' => fn() => current_user_can( 'manage_options' ),
    'args'                => [
        'title' => [
            'type'              => 'string',
            'required'          => true,
            'sanitize_callback' => 'sanitize_text_field',      // runs before callback
            'validate_callback' => fn( $v ) => is_string( $v ) && strlen( $v ) <= 200,
        ],
        'count' => [
            'type'              => 'integer',
            'sanitize_callback' => 'absint',
            'validate_callback' => fn( $v ) => is_numeric( $v ) && $v >= 0,
        ],
    ],
] );
```

---

## File Uploads

`$_FILES['type']` is user-supplied and trivially spoofed. Use `wp_check_filetype_and_ext()` to verify real MIME type and extension after `wp_handle_upload()` moves the file.

```php
add_action( 'wp_ajax_my_plugin_upload', function (): void {
    check_ajax_referer( 'my_plugin_upload', 'nonce' );
    current_user_can( 'upload_files' ) || wp_send_json_error( 'Unauthorized', 403 );

    // 'test_form' => false: nonce already verified above.
    $file = wp_handle_upload( $_FILES['my_file'], [ 'test_form' => false ] );

    if ( isset( $file['error'] ) ) {
        wp_send_json_error( $file['error'] );
    }

    // Verify real MIME type and extension — $_FILES['type'] is user-controlled.
    // $filename arg must be a filename (for extension extraction), not a URL.
    $check = wp_check_filetype_and_ext( $file['file'], basename( $file['file'] ) );
    // $mimes defaults to wp_get_mime_types() when omitted.
    if ( ! $check['type'] ) {
        wp_delete_file( $file['file'] );
        wp_send_json_error( 'File type not permitted.' );
    }

    wp_send_json_success( [ 'url' => $file['url'] ] );
} );
```

---

## Options — Sanitize Before Storing

Sanitize values before passing to `update_option()` or `update_post_meta()`. The `sanitize_option_{$option}` filter runs automatically for registered options but is not a substitute for sanitizing in your own save handler.

```php
$settings = [
    'api_key'  => sanitize_text_field( wp_unslash( $_POST['api_key'] ?? '' ) ),
    'timeout'  => absint( $_POST['timeout'] ?? 30 ),
    'endpoint' => esc_url_raw( wp_unslash( $_POST['endpoint'] ?? '' ) ),
];
update_option( 'my_plugin_settings', $settings );
```

---

## Cross-skill References

- **OWASP fundamentals, XSS/CSRF/injection theory, security headers** → `web-security` skill
- **VIP restricted functions** (eval, direct DB writes, session functions) → [`vip-standards.md`](vip-standards.md)
- **Performance-related security patterns** (uncached remote requests, N+1 queries) → [`vip-performance.md`](vip-performance.md)
