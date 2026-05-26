# Media, Theme Support, and i18n

Image sizes and post-thumbnail support, the small `theme_media.php` include, theme-support feature flags, the WP-head cleanup snippets, and the text-domain constant pattern.

## Media Support

**File:** `/inc/functions/theme_media.php`

```php
<?php

// Post thumbnail support
add_theme_support( 'post-thumbnails' );

// Custom image sizes
add_image_size( 'hero-image', 1920, 1080, true );

// Add custom sizes to media library dropdown
if ( !function_exists( "custom_image_sizes" ) ) :
function custom_image_sizes( $sizes ) {
    return array_merge( $sizes, array(
        'hero-image' => __( 'Hero Image', CUSTOM_THEME_TEXT_DOMAIN ),
    ));
}
endif;
add_filter( 'image_size_names_choose', 'custom_image_sizes' );
```

## Theme Support Features

```php
add_theme_support( 'title-tag' );
add_theme_support( 'post-thumbnails' );
add_theme_support( 'responsive-embeds' );
add_theme_support( 'html5', array( 'search-form', 'comment-form' ) );
```

## Clean Up WordPress Head

```php
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
```

## Text Domain Best Practices

```php
// Define constant in functions.php
define( 'CUSTOM_THEME_TEXT_DOMAIN', 'custom-theme' );

// Use throughout theme
__( 'Read More', CUSTOM_THEME_TEXT_DOMAIN )
the_content( __( 'Continue reading', CUSTOM_THEME_TEXT_DOMAIN ) );
```

## i18n principle

Translations always go through the text domain constant. Never hardcode user-visible strings in PHP templates — even strings that "won't be translated" today. Every `echo`, `print`, or rendered string in a template part should be wrapped in `__()`, `_e()`, or one of the escape variants (`esc_html__`, `esc_html_e`, `esc_attr__`) with `CUSTOM_THEME_TEXT_DOMAIN` as the second argument.
