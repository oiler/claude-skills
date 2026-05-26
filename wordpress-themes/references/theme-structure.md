# Theme Structure

Directory layout, the `functions.php` table-of-contents pattern, template hierarchy files, and template parts for a classic WordPress theme.

## Theme Directory Structure

```
theme-root/
├── src/
│   └── scss/
│       ├── vendor/        # Third-party CSS (reset, normalize)
│       ├── core/          # Variables, mixins, utilities
│       ├── pages/         # Page-specific CSS
│       └── styles.scss    # Main entry point
├── assets/
│   ├── css/
│   │   ├── styles.css     # Compiled main stylesheet
│   │   └── pages/         # Compiled page-specific stylesheets
│   ├── img/site/
│   └── svg/
├── inc/
│   └── functions/
│       ├── css_pagetype.php
│       ├── js_scripts.php
│       ├── theme_media.php
│       └── custom_post_types.php
├── template-parts/
│   ├── content-post.php
│   ├── content-page.php
│   ├── content-[cpt].php
│   ├── footer-markup.php
│   └── header-markup.php
├── 404.php
├── footer.php
├── functions.php          # Clean, mostly includes
├── header.php
├── index.php
├── sidebar.php
├── style.css              # Theme metadata
└── template-front.php
```

## functions.php Pattern

Keep functions.php as a clean table of contents with descriptive comments.

```php
<?php

/**
 * Theme text domain constant
 */
if ( ! defined( 'CUSTOM_THEME_TEXT_DOMAIN' ) ) {
    define( 'CUSTOM_THEME_TEXT_DOMAIN', 'custom-theme' );
}

add_theme_support( "title-tag" );
add_theme_support( "responsive-embeds" );
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );

// includes js file based on page type
require get_template_directory() . '/inc/functions/js_scripts.php';

// includes css file based on page type
require get_template_directory() . '/inc/functions/css_pagetype.php';

// media and image support
require get_template_directory() . '/inc/functions/theme_media.php';

// custom post types and taxonomies
require get_template_directory() . '/inc/functions/custom_post_types.php';
```

**CRITICAL:** Never include `flush_rewrite_rules()` in production code, even commented out.

## Template Structure

### index.php Pattern

```php
<?php get_header(); ?>

<?php 
$page_class = is_front_page() ? 'front' : 'notfront';
?>

<main id="site-content" role="main" class="<?php echo esc_attr($page_class); ?>">
    <?php 
    if ( is_singular() ) {
        if ( have_posts() ) {
            while ( have_posts() ) {
                the_post();
                get_template_part( 'template-parts/content', get_post_type() );
            }
        }
    }
    ?>
</main>

<?php get_footer(); ?>
```

### header.php Pattern

```php
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<?php get_template_part( 'template-parts/header-markup' ); ?>
```

### footer.php Pattern

```php
<?php get_template_part( 'template-parts/footer-markup' ); ?>

<?php wp_footer(); ?>
</body>
</html>
```

## Template Parts Pattern

### content-post.php

```php
<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
    <header class="entry-header">
        <?php the_title( '<h1 class="entry-title">', '</h1>' ); ?>
    </header>

    <div class="entry-content">
        <?php the_content( __( 'Continue reading', CUSTOM_THEME_TEXT_DOMAIN ) ); ?>
    </div>

    <footer class="entry-footer">
        <?php the_date(); ?>
        <?php the_author(); ?>
    </footer>
</article>
```
