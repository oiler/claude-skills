# Medical Resources Hub Theme

Custom WordPress theme for medical resource directory with custom post types and Gutenberg blocks.

---

## Basic Information

**Project:** Medical Resources Hub Theme  
**Type:** ☑ WordPress Theme  
**Purpose:** Display and filter medical resources by category, location, and specialty  
**Status:** ☑ Active Development

---

## Tech Stack

**Primary:**
- WordPress 6.4+
- PHP 8.1+
- Sass (dart-sass via Homebrew)
- Vanilla JavaScript (ES6+)

**Build Tools:**
- dart-sass for CSS compilation
- npm for package management

**Runtime:**
- PHP: 8.1+
- MySQL: 8.0+

**Browser Support:**
- Chrome/Edge >= 90, Firefox >= 88, Safari >= 14

---

## Code Standards

### WordPress
- Follow VIP compliance standards
- Modular inc/functions structure (functions.php is table of contents only)
- Use text domain constants: `THEME_TEXT_DOMAIN`
- All output escaped: `esc_html()`, `esc_attr()`, `esc_url()`
- All queries via `WP_Query` or `$wpdb->prepare()`
- Verify nonces and capabilities on form submissions
- Prefix all functions: `mrh_`

### CSS/Sass
- Semantic, well-named classes (avoid utility frameworks)
- Maximum 2-3 levels of nesting
- Three-folder structure: vendor/, core/, pages/
- BEM naming: `.block__element--modifier`
- Compile: `sass-build` (alias for `sass --watch sass:. --style compressed`)

### JavaScript
- Functional patterns over classes
- ES6+ features (no polyfills needed)
- Modular, reusable code
- No jQuery dependencies

### Git
- Atomic commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Interactive rebase for clean history
- Force push with `--force-with-lease` only

---

## Project Structure

```
theme-root/
├── inc/
│   ├── functions/
│   │   ├── setup.php              # Theme setup and support
│   │   ├── enqueue.php            # Scripts and styles
│   │   ├── custom-post-types.php  # Resources CPT
│   │   ├── taxonomies.php         # Categories, locations
│   │   ├── blocks.php             # Block registration
│   │   └── security.php           # Security headers, nonces
│   └── blocks/
│       ├── resource-card/
│       │   ├── block.json
│       │   ├── render.php
│       │   └── editor.js
│       └── resource-filter/
├── sass/
│   ├── vendor/                    # Third-party styles
│   ├── core/                      # Variables, mixins, base
│   │   ├── _variables.scss
│   │   ├── _mixins.scss
│   │   └── _reset.scss
│   ├── pages/                     # Page-specific styles
│   │   ├── _archive-resources.scss
│   │   └── _single-resource.scss
│   └── style.scss                 # Main entry (imports all)
├── js/
│   ├── modules/
│   │   ├── resource-filter.js
│   │   └── map-display.js
│   └── main.js                    # Entry point
├── template-parts/
│   ├── content-resource.php
│   └── resource-filters.php
├── functions.php                  # Table of contents only
├── style.css                      # Theme header (required)
├── index.php                      # Fallback template
├── archive-resource.php           # Resources archive
└── single-resource.php            # Single resource
```

---

## Key Patterns & Conventions

### Custom Post Type Registration
```php
// In inc/functions/custom-post-types.php
function mrh_register_resource_post_type() {
    $args = [
        'labels' => mrh_get_resource_labels(),
        'public' => true,
        'has_archive' => true,
        'supports' => ['title', 'editor', 'thumbnail'],
        'show_in_rest' => true,
        'rewrite' => ['slug' => 'resources'],
    ];
    register_post_type('resource', $args);
}
add_action('init', 'mrh_register_resource_post_type');
```

### Enqueueing Assets
```php
// In inc/functions/enqueue.php
function mrh_enqueue_assets() {
    wp_enqueue_style(
        'mrh-main',
        get_stylesheet_uri(),
        [],
        filemtime(get_stylesheet_directory() . '/style.css')
    );
    
    wp_enqueue_script(
        'mrh-main',
        get_template_directory_uri() . '/js/main.js',
        [],
        filemtime(get_template_directory() . '/js/main.js'),
        true
    );
}
add_action('wp_enqueue_scripts', 'mrh_enqueue_assets');
```

### Custom Block (Server-Side Rendering)
```php
// In inc/blocks/resource-card/render.php
<?php
$resource_id = $block->context['postId'] ?? get_the_ID();
$title = get_the_title($resource_id);
$location = get_field('location', $resource_id);
?>
<div class="resource-card">
    <h3 class="resource-card__title"><?php echo esc_html($title); ?></h3>
    <p class="resource-card__location"><?php echo esc_html($location); ?></p>
</div>
```

---

## Testing Requirements

**Priority Areas:**
1. Resource filtering and search functionality (high risk)
2. Custom post type registration and queries (medium risk)
3. User input sanitization in search/filters (security critical)

**Test Types Enabled:**
- ☑ Unit tests (target: 70%)
- ☑ Integration tests
- ☑ Security tests (always required)

**Critical Test Scenarios:**
1. Filter resources by multiple taxonomies simultaneously
2. Handle empty search results gracefully
3. Prevent SQL injection in custom queries
4. Verify proper escaping of user-generated content
5. Test resource archive pagination

---

## Development Commands

```bash
# Watch and compile Sass
sass-build

# Or manually
sass --watch sass:. --style compressed

# Start local WordPress
# (Using Local, MAMP, or wp-env)
```

---

## Environment Setup

**Required:**
- WordPress 6.4+
- PHP 8.1+
- MySQL 8.0+
- Homebrew (for dart-sass)
- Node/npm (for build tools)

**Configuration:**
```php
// In wp-config.php
define('THEME_TEXT_DOMAIN', 'medical-resources-hub');
define('MRH_VERSION', '1.0.0');
```

---

## Security Checklist

- ☑ Input validation on search/filter forms
- ☑ Output escaping (`esc_html`, `esc_attr`, `esc_url`)
- ☑ SQL injection prevention (`$wpdb->prepare()`)
- ☑ CSRF protection (nonces on all forms)
- ☑ XSS prevention (escape all output)
- ☑ Capability checks on admin functions
- ☑ Sanitize file uploads (if applicable)

---

## Common Gotchas

**Issue:** Custom post type not showing in REST API for Gutenberg
- Solution: Add `'show_in_rest' => true` to CPT registration args

**Issue:** Sass not compiling on save
- Solution: Check `sass-build` alias is running; verify file paths in scss imports

**Issue:** Custom taxonomy terms not saving with posts
- Solution: Ensure `register_taxonomy()` called before `register_post_type()`

**Issue:** Blocks not appearing in editor
- Solution: Verify `block.json` has correct `apiVersion` and block is registered in `blocks.php`

---

## Claude Instructions

### Skills to Use
- ☑ css-specialist (for Sass architecture)
- ☑ web-security (for input/output handling)
- ☑ wordpress-blocks (for Gutenberg development)
- ☑ wordpress-themes (for theme structure)

### Testing Approach
- Write tests for: All custom queries, user input handling, block rendering
- Test automatically: New functions in inc/functions/, new blocks
- Skip testing: Standard WordPress template files, simple display logic

### Code Generation Preferences
- Comment level: ☑ Only complex logic
- Explanation style: ☑ Brief
- Pattern to follow: VIP coding standards, modular inc/functions structure

---

## Quick Reference

### Key Files
- `functions.php` - Table of contents (includes only)
- `inc/functions/setup.php` - Theme setup, add_theme_support()
- `inc/functions/custom-post-types.php` - Resources CPT
- `inc/functions/blocks.php` - Block registration
- `sass/style.scss` - Main Sass entry point

### External Resources
- [WordPress VIP Documentation](https://docs.wpvip.com/technical-references/code-quality/)
- [Block Editor Handbook](https://developer.wordpress.org/block-editor/)
- [Theme Handbook](https://developer.wordpress.org/themes/)

### Text Domain / Namespace
- Text domain: `medical-resources-hub`
- Function prefix: `mrh_`
- Constant: `THEME_TEXT_DOMAIN`

---

## Notes & Decisions

**2026-01-19**: Decided to use server-side rendering for all custom blocks to reduce JavaScript complexity and improve performance. All block rendering logic in `/inc/blocks/{block-name}/render.php`.

**2026-01-19**: Using Advanced Custom Fields (ACF) for resource metadata (location, contact info, specialties). Fields registered in code via `acf/init` hook in `inc/functions/setup.php`.

**2026-01-19**: Taxonomies: `resource_category` (hierarchical), `resource_location` (non-hierarchical), `specialty` (non-hierarchical). Registered in `inc/functions/taxonomies.php`.
