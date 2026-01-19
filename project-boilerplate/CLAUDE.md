# Project Name

Brief description of what this project does.

## Tech Stack
- WordPress 6.x (custom theme)
- PHP 8.1+
- Sass (dart-sass via Homebrew)
- Vanilla JavaScript (ES6+)

## Code Standards

### WordPress
- Follow VIP compliance standards
- Modular inc/functions structure (functions.php is table of contents only)
- Use text domain constants
- All output must be escaped (esc_html, esc_attr, esc_url)
- All database queries via WP_Query or $wpdb->prepare()
- Verify nonces and capabilities on form submissions

### CSS/Sass
- Semantic, well-named classes (avoid utility frameworks)
- Maximum 2-3 levels of nesting
- Three-folder structure: vendor, core, pages
- Compile with: `sass-build` (see package.json)

### JavaScript
- Functional patterns preferred over classes
- ES6+ features (supported since 2017)
- No polyfills needed
- Modular, reusable code

### Git
- Atomic commits with clear messages
- Interactive rebase for clean history
- Force push with --force-with-lease only

## Security Requirements
- Sanitize all user input before storage
- Escape all output (context-appropriate)
- Use prepared statements for all queries
- Verify nonces and capabilities
- No secrets in code (use wp-config.php constants)

## Project Structure
```
/inc
  /functions
    - setup.php          # Theme setup and support
    - enqueue.php        # Scripts and styles
    - custom-post-types.php
    - taxonomies.php
    - blocks.php         # Gutenberg block registration
/sass
  /vendor              # Third-party styles
  /core                # Base styles, variables, mixins
  /pages               # Page-specific styles
  - style.scss         # Main entry point
/js
  /modules             # Reusable JS modules
  - main.js           # Main entry point
/template-parts       # Reusable template components
/blocks               # Custom Gutenberg blocks
```

## Development Workflow

### Build CSS
```bash
sass-build  # Custom alias: sass --watch sass:. --style compressed
```

### WordPress Development
1. Create functions in appropriate /inc/functions/ file
2. Include in functions.php table of contents
3. Test in local environment
4. Verify VIP compliance

### Custom Blocks
- Use server-side rendering
- Register with block.json
- Keep PHP rendering logic in /blocks/{block-name}/render.php

## Environment
- WordPress 6.4+
- PHP 8.1+
- MySQL 8.0+
- Node/npm for build tools

## Key Patterns

### Custom Post Type Registration
Use standard WordPress pattern in /inc/functions/custom-post-types.php

### Enqueueing Assets
Always use wp_enqueue_style/script with proper dependencies and versioning

### Database Queries
Prefer WP_Query over direct $wpdb queries when possible
Always use $wpdb->prepare() for custom queries

## Notes
- Text domain: 'theme-slug'
- Prefix custom functions with theme_slug_
- Document complex logic with inline comments