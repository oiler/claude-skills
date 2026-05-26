# WordPress VIP Compliance

> For general OWASP / XSS / CSRF fundamentals, see the `web-security` skill. This file covers WordPress-specific escape/sanitize APIs and the VIP checklist.

VIP-compliant escape/sanitize discipline, file-path handling, and the pre-deploy checklist for classic themes. Targets the WordPress VIP Coding Standards as of 2025.

## Always Escape Output

```php
// Text content
echo esc_html( $text );

// HTML attributes
echo esc_attr( $class );

// URLs
echo esc_url( $url );

// Translation functions with escaping
esc_html__( 'Text', CUSTOM_THEME_TEXT_DOMAIN )
esc_attr__( 'Text', CUSTOM_THEME_TEXT_DOMAIN )
esc_html_e( 'Text', CUSTOM_THEME_TEXT_DOMAIN )
```

## Always Sanitize Input

```php
// Text fields
$value = sanitize_text_field( $_POST['field'] );

// URLs
$url = esc_url_raw( $_POST['url'] );

// Integers
$id = absint( $_POST['id'] );
```

## Proper File Paths

```php
// CORRECT: Use WordPress functions
get_template_directory()        // /path/to/theme
get_template_directory_uri()    // https://site.com/wp-content/themes/theme

// WRONG: Never hardcode paths
```

## Text Domain Best Practices

```php
// Define constant in functions.php
define( 'CUSTOM_THEME_TEXT_DOMAIN', 'custom-theme' );

// Use throughout theme
__( 'Read More', CUSTOM_THEME_TEXT_DOMAIN )
the_content( __( 'Continue reading', CUSTOM_THEME_TEXT_DOMAIN ) );
```

## VIP Compliance Checklist

**Before deploying:**

- [ ] All output is escaped (`esc_html()`, `esc_attr()`, `esc_url()`)
- [ ] All input is sanitized
- [ ] Scripts/styles properly enqueued with versions
- [ ] Text domain constant defined and used throughout
- [ ] No `flush_rewrite_rules()` in code
- [ ] File paths use WordPress functions
- [ ] No hardcoded URLs or paths
- [ ] Template parts used for modular structure
- [ ] Theme versioning for cache busting
