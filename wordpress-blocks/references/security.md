# Block Security and VIP Compliance

Escape on output, sanitize on input. Every attribute pulled from a block must pass through the appropriate `esc_*()` or `wp_kses_*()` function at the echo site (not at variable assignment). Cast IDs through `absint()` before use. For non-block AJAX, web request handling, or broader OWASP coverage, see the `web-security` skill.

## Always Escape Output in PHP

Escape at the echo site, not at variable assignment. The old "pre-escape into a variable, then echo trusted" pattern is safe but fragile — the next person to touch the code can echo `$title` unescaped without a linter or reviewer noticing. Escape where the value enters HTML.

| Context | Function | Example |
|---|---|---|
| Plain text | `esc_html()` | `<?php echo esc_html($title); ?>` |
| HTML attribute value | `esc_attr()` | `<div class="<?php echo esc_attr($class); ?>">` |
| URLs in `href` / `src` | `esc_url()` | `<a href="<?php echo esc_url($link); ?>">` |
| Multi-paragraph text (preserves formatting) | `wp_kses_post()` + `wpautop()` | `<?php echo wp_kses_post(wpautop($body)); ?>` |
| Inside `<script>` (rare, prefer `wp_localize_script`) | `wp_json_encode()` | `<?php echo wp_json_encode($data); ?>` |

**Wrong:** escape during assignment, echo "trusted":
```php
$title = isset($attributes['title']) ? esc_html($attributes['title']) : '';
// 200 lines later...
echo $title; // safe today, fragile forever
```

**Right:** assign raw, escape on output:
```php
$title = $attributes['title'] ?? '';
echo esc_html($title);
```

PHP 8.1+ `??` null-coalescing replaces the older `isset(...)` ternary throughout.

## Always Sanitize in PHP

```php
// Integers (for image IDs, etc.)
$image_id = isset($attributes['imageId']) ? absint($attributes['imageId']) : 0;

// Numbers
$count = isset($attributes['count']) ? intval($attributes['count']) : 0;
```

## Proper Asset Paths

```php
// CORRECT:
get_template_directory_uri() . '/inc/blocks/js/block-name.js'
get_template_directory_uri() . '/assets/img/site/hero.jpg'

// Use filemtime for cache busting
filemtime(get_template_directory() . '/inc/blocks/js/block-name.js')
```

## Required JavaScript Dependencies

```php
wp_enqueue_script(
    'block-name-block',
    get_template_directory_uri() . '/inc/blocks/js/block-name.js',
    array(
        'wp-blocks',           // Core block functionality
        'wp-element',          // React elements
        'wp-block-editor',     // Block editor components (required for MediaUpload)
        'wp-components',       // UI components
    ),
    filemtime(get_template_directory() . '/inc/blocks/js/block-name.js'),
    false // Load in header for editor
);
```

## Nonces

Server-side render callbacks (`render_callback`) don't need nonces — Gutenberg handles the editor save round-trip and authorization through core. You only need nonces if your block adds **custom AJAX** in editor JS (e.g., a "test connection" button that hits a custom REST endpoint).

For custom AJAX:

```php
// Print nonce into the page (or pass via wp_localize_script)
wp_localize_script('block-name-block', 'blockNameData', array(
    'nonce'   => wp_create_nonce('block_name_action'),
    'ajaxUrl' => admin_url('admin-ajax.php'),
));

// In the AJAX handler:
function handle_block_name_ajax() {
    check_ajax_referer('block_name_action', 'nonce');
    if (! current_user_can('edit_posts')) {
        wp_send_json_error('forbidden', 403);
    }
    // ... do the thing
    wp_send_json_success(array('result' => 'ok'));
}
add_action('wp_ajax_block_name_action', 'handle_block_name_ajax');
```

For broader AJAX, REST, and request-handling security beyond blocks, see the `web-security` skill.

## VIP gotchas

- Never `extract($attributes)` — drops them into the symbol table where escaping is easy to forget.
- Never trust `wp_unslash()` to make data safe — it only reverses WordPress's magic quotes; it does NOT sanitize.
- Always cast image IDs through `absint()` before passing to `wp_get_attachment_image_url()` or any DB function — Gutenberg may persist them as strings.
- If the render reads anything user-restricted (private posts, draft excerpts, capability-gated copy), guard with `current_user_can()` — block render runs in the frontend request context and inherits whatever the viewer can see.
- Avoid `echo $attributes['raw']` in any form, even "for debugging." Logged debug output ships to production more often than you'd think.
- When emitting inline styles, escape the value with `esc_attr()` AND validate the property if it's user-controlled (`'color' => $value` without validation lets attackers inject arbitrary CSS).
