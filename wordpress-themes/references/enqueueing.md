# Enqueueing Styles and Scripts

WordPress-native enqueueing for a classic theme: global + page-specific stylesheets and scripts, with consistent handle naming and version-based cache-busting.

## CSS Enqueueing

**File:** `/inc/functions/css_pagetype.php`

```php
<?php
// Global styles
if ( !function_exists ( "custom_theme_css_global" ) ) :
function custom_theme_css_global() {
    $theme_version = wp_get_theme()->get( "Version" );
    wp_enqueue_style( 
        "custom-theme-global", 
        get_template_directory_uri() . "/assets/css/styles.css", 
        array(), 
        $theme_version 
    );
}
add_action( "wp_enqueue_scripts", "custom_theme_css_global", 10 );
endif;

// Page-specific styles
if ( !function_exists ( "custom_theme_css_by_page_type" ) ) :
function custom_theme_css_by_page_type() {
    $theme_version = wp_get_theme()->get( "Version" );
    
    if ( is_front_page() || is_page('front-page') ) {
        wp_enqueue_style( 
            "custom-theme-front", 
            get_template_directory_uri() . "/assets/css/pages/front.css", 
            array(), 
            $theme_version 
        );
    }
}
add_action( "wp_enqueue_scripts", "custom_theme_css_by_page_type", 20 );
endif;
```

**Key Points:**
- Use theme version for cache busting
- Consistent handle naming (`custom-theme-*`)
- Page-specific CSS loaded conditionally
- Priority ordering (global at 10, specific at 20)

## JavaScript Enqueueing

**File:** `/inc/functions/js_scripts.php`

```php
<?php
if ( !function_exists ( "custom_theme_js_global" ) ) :
function custom_theme_js_global() {
    $theme_version = wp_get_theme()->get( 'Version' );
    
    // Main scripts: load in footer
    // wp_enqueue_script( 
    //     'theme-main', 
    //     get_template_directory_uri() . '/assets/js/app.js', 
    //     array(), 
    //     $theme_version, 
    //     true 
    // );
}
add_action('wp_enqueue_scripts', 'custom_theme_js_global');
endif;
```

**Key Points:**
- Always pass array for dependencies (even if empty)
- Always pass version for cache busting
- Use `true` for footer loading (better performance)

## Why the version argument matters

The dependencies array is required even when empty — `wp_enqueue_style` and `wp_enqueue_script` both expect it as the third argument. The version (fourth argument) is appended as a query string to the asset URL (e.g., `styles.css?ver=1.4.2`), which is how browsers know to invalidate their cache when the theme's `style.css` Version bumps. Without a version, browsers may serve stale assets indefinitely.
