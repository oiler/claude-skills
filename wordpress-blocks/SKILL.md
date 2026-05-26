---
name: wordpress-blocks
description: WordPress custom Gutenberg block development with server-side PHP rendering and no build toolchain. Use when user asks to build, register, or modify WordPress blocks, work with `register_block_type()`, write a `render_callback`, add a `MediaUpload`/`MediaUploadCheck` image picker, create blocks with repeating items, escape or sanitize block output for WP VIP compliance, set up editor UI with WP components (`TextControl`, `TextareaControl`, `Button`), or enqueue block editor assets. Covers WordPress 6.5+ / PHP 8.1+. Teaches PHP-side `attributes` arrays plus vanilla JS using `wp.element` (no `block.json`, no JSX, no `@wordpress/scripts`).
---

# WordPress Custom Gutenberg Blocks

Build custom Gutenberg blocks for WordPress themes that give content editors control over text and media while developers retain control over layout and design.

## Block Development Philosophy

**Editors Control:**
- Text content (headers, descriptions, body copy)
- Links and CTAs
- Images (via WordPress media uploader)

**Developers Control:**
- HTML structure and markup
- CSS styling and layout
- JavaScript functionality
- Design consistency

**Benefits:**
- Consistent design across the site
- Easy content updates without developer intervention
- Reduced risk of breaking layouts
- Cleaner, more maintainable codebase

## Platform baseline

This skill assumes **WordPress 6.5+** and **PHP 8.1+**. WP 6.5 (April 2024) is the right cutoff for blocks work in 2026 — earlier releases miss block-editor APIs this skill relies on. PHP 8.1+ is required by WP 6.5 itself and unlocks readonly properties, enums, and `never` return types if your render functions want them.

## Routing — read the right reference

| User wants to... | Read first |
|---|---|
| Add or change attribute types (text, number, textarea, boolean) | [references/attributes.md](references/attributes.md) |
| Add an image picker to a block | [references/media-upload.md](references/media-upload.md) |
| Build a block with repeating items (multiple cards, list items) | [references/multiple-items.md](references/multiple-items.md) |
| Audit escaping, sanitization, asset paths, or JS deps for VIP | [references/security.md](references/security.md) |

## Block file structure

Each block consists of three files:

```
inc/blocks/
├── block-name.php           # PHP registration and render
├── js/
│   └── block-name.js        # Editor JavaScript
└── css/                     # Optional
    └── block-name.css       # Block-specific styles
```

**Register block in functions.php:**
```php
// custom gutenberg blocks
require get_template_directory() . '/inc/blocks/hp-lede.php';
```

## Minimal block template

A complete copy-pasteable starting point. Escape at the echo site, not at variable assignment — see [security.md](references/security.md) for the full rationale.

### PHP Registration File

**File:** `/inc/blocks/block-name.php`

```php
<?php
/**
 * Block Name Block
 */

function register_block_name_block() {
    register_block_type('theme/block-name', array(
        'render_callback' => 'render_block_name_block',
        'attributes' => array(
            'blockTitle' => array(
                'type' => 'string',
                'default' => 'Default Title'
            ),
            'blockDescription' => array(
                'type' => 'string',
                'default' => 'Default description text.'
            ),
            'blockLink' => array(
                'type' => 'string',
                'default' => '/default-link/'
            ),
        ),
    ));
}
add_action('init', 'register_block_name_block');

function render_block_name_block($attributes) {
    $block_title = $attributes['blockTitle'] ?? '';
    $block_description = $attributes['blockDescription'] ?? '';
    $block_link = $attributes['blockLink'] ?? '';

    ob_start();
    ?>
    <section class="block-name">
        <h2><?php echo esc_html($block_title); ?></h2>
        <p><?php echo esc_html($block_description); ?></p>
        <a href="<?php echo esc_url($block_link); ?>" class="button">Learn More</a>
    </section>
    <?php
    return ob_get_clean();
}

function enqueue_block_name_block_editor_assets() {
    wp_enqueue_script(
        'block-name-block',
        get_template_directory_uri() . '/inc/blocks/js/block-name.js',
        array('wp-blocks', 'wp-element', 'wp-block-editor', 'wp-components'),
        filemtime(get_template_directory() . '/inc/blocks/js/block-name.js'),
        false
    );
}
add_action('enqueue_block_editor_assets', 'enqueue_block_name_block_editor_assets');
```

### JavaScript Editor File

**File:** `/inc/blocks/js/block-name.js`

```javascript
(function(wp) {
    const { registerBlockType } = wp.blocks;
    const { TextControl, TextareaControl } = wp.components;
    const { createElement: el } = wp.element;

    registerBlockType('theme/block-name', {
        title: 'Block Name',
        icon: 'admin-post',
        category: 'common',
        attributes: {
            blockTitle: {
                type: 'string',
                default: 'Default Title'
            },
            blockDescription: {
                type: 'string',
                default: 'Default description text.'
            },
            blockLink: {
                type: 'string',
                default: '/default-link/'
            }
        },

        edit: function(props) {
            const { attributes, setAttributes } = props;

            return el('div', {
                className: 'block-name-editor',
                style: { padding: '20px', border: '1px solid #ddd' }
            },
                el('h3', {}, 'Block Name'),

                el(TextControl, {
                    label: 'Block Title',
                    value: attributes.blockTitle,
                    onChange: function(value) {
                        setAttributes({ blockTitle: value });
                    }
                }),

                el(TextareaControl, {
                    label: 'Description',
                    value: attributes.blockDescription,
                    onChange: function(value) {
                        setAttributes({ blockDescription: value });
                    },
                    rows: 4
                }),

                el(TextControl, {
                    label: 'Link',
                    value: attributes.blockLink,
                    onChange: function(value) {
                        setAttributes({ blockLink: value });
                    }
                })
            );
        },

        save: function() {
            return null; // Using PHP render callback
        }
    });
})(window.wp);
```

## Block icons

Common Dashicons for blocks:

```javascript
icon: 'admin-post'      // Document
icon: 'megaphone'       // Announcement/Lede
icon: 'admin-links'     // Resources/Links
icon: 'info'            // Information
icon: 'warning'         // Urgent/Warning
icon: 'games'           // Sports/Games
icon: 'awards'          // Achievement
icon: 'media-document'  // Article
```

## Editor styling tips

### Add Visual Hierarchy in Editor

```javascript
el('div', {
    className: 'block-editor',
    style: { padding: '20px', border: '1px solid #ddd' }
},
    el('h3', {}, 'Block Title'),
    el('hr'),
    el('h4', {}, 'Section 1'),
    // fields...
    el('hr'),
    el('h4', {}, 'Section 2'),
    // more fields...
)
```

### Add Preview in Editor

```javascript
el('div', { style: { marginTop: '15px', padding: '10px', backgroundColor: '#f0f0f0' } },
    el('strong', {}, 'Preview:'),
    el('p', { style: { marginTop: '10px' } }, attributes.description)
)
```

## A note on block.json

`block.json` is WordPress's canonical modern manifest for registering blocks. This skill teaches the PHP-only `register_block_type()` approach because it requires no build toolchain — no `@wordpress/scripts`, no JSX, no npm. If your project already uses `@wordpress/scripts` or you want JSX, see the [WordPress block-editor handbook](https://developer.wordpress.org/block-editor/reference-guides/block-api/block-metadata/) — this skill doesn't cover that path.

## Quick Reference

### Block Registration Checklist

- [ ] PHP file in `/inc/blocks/`
- [ ] JavaScript file in `/inc/blocks/js/`
- [ ] Block registered with `register_block_type()`
- [ ] Render callback function created
- [ ] All attributes defined with types and defaults
- [ ] All output escaped at the echo site (`esc_html()`, `esc_url()`, `esc_attr()`)
- [ ] Editor assets enqueued with dependencies (including `wp-block-editor` if using `MediaUpload`)
- [ ] Block added to functions.php includes
- [ ] Icon and category specified
- [ ] `save` function returns `null` (using PHP render)

### Common JavaScript Components

```javascript
const { registerBlockType } = wp.blocks;
const { TextControl, TextareaControl, ToggleControl, Button } = wp.components;
const { MediaUpload, MediaUploadCheck } = wp.blockEditor;
const { createElement: el } = wp.element;
```

### Attribute Type Reference

```php
'string'  => array('type' => 'string',  'default' => '')
'number'  => array('type' => 'number',  'default' => 0)
'boolean' => array('type' => 'boolean', 'default' => false)
'array'   => array('type' => 'array',   'default' => array())
'object'  => array('type' => 'object',  'default' => array())
```
