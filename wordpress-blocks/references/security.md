# Block Security and VIP Compliance

Escape on output, sanitize on input. Every attribute pulled from a block must pass through the appropriate `esc_*()` or `wp_kses_*()` function at the echo site (not at variable assignment). Cast IDs through `absint()` before use. For non-block AJAX, web request handling, or broader OWASP coverage, see the `web-security` skill.

## Always Escape Output in PHP

```php
// Text
$title = isset($attributes['title']) ? esc_html($attributes['title']) : '';

// Attributes
$class = isset($attributes['className']) ? esc_attr($attributes['className']) : '';

// URLs
$link = isset($attributes['link']) ? esc_url($attributes['link']) : '';

// Multi-paragraph text (preserves formatting)
$description = isset($attributes['description']) ? wp_kses_post(wpautop($attributes['description'])) : '';
```

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
    'block-name',
    get_template_directory_uri() . '/inc/blocks/js/block-name.js',
    array(
        'wp-blocks',      // Core block functionality
        'wp-element',     // React elements
        'wp-editor',      // Editor components
        'wp-components',  // UI components
        'wp-block-editor' // For MediaUpload
    ),
    filemtime(get_template_directory() . '/inc/blocks/js/block-name.js'),
    false // Load in header for editor
);
```
