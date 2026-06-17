# VIP Coding Standards (VIPCS)

WordPress VIP plugin linting, restricted function categories, and platform-only constraints. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025) / VIPCS 3.0+.

---

## Ruleset Overview

**Package:** `automattic/vipwpcs` (VIPCS 3.0+)

VIPCS layers two rulesets on top of WordPress Coding Standards (WPCS, `wp-coding-standards/wpcs`):

| Ruleset | Enforces |
|---------|---------|
| `WordPressVIPMinimum` | VIP-required rules — restricted functions, performance, security patterns |
| `WordPress-VIP-Go` | Extends `WordPressVIPMinimum`; includes the full WordPress core standards |

The scaffolder emits `phpcs.xml.dist` and `composer.json` pre-wired with both rulesets.

---

## Install

```bash
composer require --dev automattic/vipwpcs dealerdirect/phpcodesniffer-composer-installer
```

The `dealerdirect/phpcodesniffer-composer-installer` plugin auto-registers PHPCS standard paths — no manual `phpcs --config-set installed_paths` step.

```bash
composer lint   # phpcs  — report violations
composer fix    # phpcbf — auto-fix what it can
```

---

## `phpcs.xml.dist` (as emitted by the scaffolder)

```xml
<?xml version="1.0"?>
<ruleset name="My Plugin">
    <description>PHPCS ruleset for My Plugin — WordPress VIP standards.</description>

    <!-- Scan all PHP files in the project root. -->
    <file>.</file>

    <!-- Exclude generated / third-party code. -->
    <exclude-pattern>*/vendor/*</exclude-pattern>
    <exclude-pattern>*/node_modules/*</exclude-pattern>

    <!-- Target PHP 8.1+. -->
    <config name="testVersion" value="8.1-"/>

    <!-- WordPress text domain and function prefix for i18n / naming checks. -->
    <config name="text_domain" value="my-plugin"/>

    <rule ref="WordPress-VIP-Go"/>
    <rule ref="WordPressVIPMinimum"/>
    <rule ref="WordPress-Docs"/>

    <!-- Set the expected text domain for i18n rules. -->
    <rule ref="WordPress.WP.I18n">
        <properties>
            <property name="text_domain" type="array" value="my-plugin"/>
        </properties>
    </rule>

    <!-- Enforce namespace/prefix to avoid collisions. -->
    <rule ref="WordPress.NamingConventions.PrefixAllGlobals">
        <properties>
            <property name="prefixes" type="array" value="My_Plugin"/>
        </properties>
    </rule>
</ruleset>
```

Key directives:

- `<file>.</file>` + `exclude-pattern` — scans from project root, strips `vendor/` and `node_modules/`.
- `testVersion` — tells PHPCompatibility sniffs which PHP floor to enforce (8.1+).
- `WordPress-VIP-Go` extends `WordPressVIPMinimum`; listing both is explicit and valid.
- `WordPress-Docs` — enforces PHPDoc on classes and methods.

---

## Restricted / Discouraged Function Categories

`WordPressVIPMinimum` flags these patterns. Each entry shows the wrong pattern and the compliant alternative.

### Direct Filesystem Writes

Direct PHP filesystem functions bypass the WP abstraction layer and are unsafe on VIP (the platform filesystem is read-only outside `wp-content/uploads`).

```php
// Wrong
file_put_contents( '/tmp/data.txt', $content );
$fh = fopen( '/tmp/data.txt', 'w' );
fwrite( $fh, $content );
unlink( '/tmp/data.txt' );

// Right — use WP Filesystem API
global $wp_filesystem;
WP_Filesystem();
$wp_filesystem->put_contents( $upload_dir['path'] . '/data.txt', $content, FS_CHMOD_FILE );

// Right — for uploaded files
$upload_dir = wp_upload_dir();
// then move the temp file with move_uploaded_file() into $upload_dir['path']
// or use wp_handle_upload() to do it in one call
```

> On VIP Platform, only `wp-content/uploads` is writable. `wp_upload_dir()` always returns a path within that writable subtree. See also the [VIP-Platform-only section](#vip-platform-only-constraints) below.

### Dynamic Code Execution

`eval()` and `create_function()` are forbidden — no safe form exists.

```php
// Wrong
eval( $user_input );
$fn = create_function( '$x', 'return $x * 2;' );

// Right — refactor to a named function or closure
$fn = fn( int $x ): int => $x * 2;
```

### Direct Database Access (Unprepared SQL)

`$wpdb->query()` with string concatenation is flagged. Use `$wpdb->prepare()` for any query with variable input; prefer core API wrappers over raw SQL where possible.

```php
// Wrong
$wpdb->query( "SELECT * FROM {$wpdb->posts} WHERE post_title = '" . $title . "'" );

// Right — prepared statement
$wpdb->get_results(
    $wpdb->prepare(
        "SELECT * FROM %i WHERE post_title = %s",
        $wpdb->posts,
        $title
    )
);

// Better — use WP_Query instead of raw SQL for posts
$query = new WP_Query( [ 'post_title' => $title, 'post_type' => 'post' ] );
```

For input/output escaping and nonce/caps checks, see [`security.md`](security.md).

### `query_posts()`

`query_posts()` replaces `$wp_query` globally, breaking pagination and other plugins that depend on the main query object.

```php
// Wrong
query_posts( 'post_type=event&posts_per_page=5' );

// Right — use WP_Query for secondary queries
$events = new WP_Query( [ 'post_type' => 'event', 'posts_per_page' => 5 ] );

// Right — modify the main query before it runs
add_action( 'pre_get_posts', function ( WP_Query $q ): void {
    if ( $q->is_main_query() && ! is_admin() && $q->is_post_type_archive( 'event' ) ) {
        $q->set( 'posts_per_page', 5 );
    }
} );
```

### `extract()`

`extract()` injects an arbitrary number of variables into the current scope with opaque names — a source of variable shadowing bugs and a security risk when the source array is user-influenced.

```php
// Wrong
extract( $data ); // $data['title'] silently becomes $title

// Right — reference array keys explicitly
$title       = $data['title'] ?? '';
$description = $data['description'] ?? '';
```

### Uncached Remote Requests

`wp_remote_get()` and related functions inside a page-load cycle without a caching layer hit the remote endpoint on every request. VIPCS discourages uncached remote calls outside background jobs.

```php
// Wrong — fetches on every request
$response = wp_remote_get( 'https://api.example.com/data' );

// Right — wrap in a transient
$cache_key = 'my_plugin_api_data';
$data = get_transient( $cache_key );
if ( false === $data ) {
    $response = wp_remote_get( 'https://api.example.com/data' );
    if ( ! is_wp_error( $response ) ) {
        $data = wp_remote_retrieve_body( $response );
        set_transient( $cache_key, $data, HOUR_IN_SECONDS );
    }
}
```

See [`vip-performance.md`](vip-performance.md) for object cache patterns and full remote-request guidance.

### Session and Cookie Functions

PHP's native `session_start()`, `$_SESSION`, and direct `setcookie()` calls conflict with full-page caching and are flagged on VIP. Use WordPress's own mechanisms: `update_user_meta()` for logged-in state; transients or WP auth cookies for anonymous state.

### Performance-Sensitive Functions in Loops

Functions like `get_term_link()`, `wp_get_post_terms()`, and `attachment_url_to_postid()` trigger database queries per call. Calling them inside a loop multiplies the query count with the result set size (N+1 problem). VIPCS flags this pattern.

```php
// Wrong — query per post
foreach ( $posts as $post ) {
    $terms = wp_get_post_terms( $post->ID, 'category' );
    // ... render
}

// Right — collect IDs, fetch once, map by post ID
$post_ids = wp_list_pluck( $posts, 'ID' );
// Use a single WP_Query with tax_query, or prime the cache:
update_post_term_cache( $post_ids, 'post' );
foreach ( $posts as $post ) {
    $terms = get_the_terms( $post->ID, 'category' ); // reads from warm cache
}
```

---

## VIP-Platform-only Constraints

> **These constraints apply on WordPress VIP Platform (VIP Go). Self-hosting relaxes all of them.**

### Read-only Filesystem

The VIP Platform filesystem is read-only except for `wp-content/uploads`. Use the WP Filesystem API (`WP_Filesystem`) for any writes; use `wp_upload_dir()` to resolve the writable uploads path dynamically. Do not hardcode `/tmp` or relative paths. See the [Direct Filesystem Writes](#direct-filesystem-writes) section for the correct pattern.

### Must-Use Plugins (`mu-plugins`)

Files in `wp-content/mu-plugins/` are loaded automatically before regular plugins and cannot be deactivated from the admin. Characteristics:

- No activation/deactivation hooks fire (WordPress never "activates" them).
- Load order is filename-alphabetical within `mu-plugins/`.
- Subdirectory support requires a loader stub: create `mu-plugins/my-plugin-loader.php` that manually `require`s the plugin's main file.

**When to use mu-plugins:** platform-wide code that must always be present (logging, request routing, shared helpers). For everything else, use a regular plugin — it stays manageable, testable, and configurable without a deploy.

### No Long-Running Processes

VIP enforces PHP execution time limits. Long-running operations (bulk data migrations, large file processing) must be broken into WP-Cron batches or handed off to external jobs. Do not assume indefinite execution time.

### No Custom Database Tables Without Review

Creating custom tables requires a VIP Platform review. Prefer post meta, options, and term meta for structured data. If a custom table is genuinely necessary, open a VIP support request before building.

### PR-Based Code-Review Deploy Flow

Code reaches VIP production through a pull-request review process — VIP engineers review every merge before it deploys. There is no FTP or direct SSH deploy. Design changes to be reviewable: small PRs, clear commit messages, no minified blobs committed.

### Committed `vendor/`

VIP Go does not run `composer install` at deploy time. The `vendor/` directory must be committed to the repository. The scaffolder configures `.gitignore` and `.gitattributes` for this correctly. See `structure-and-scaffolding.md` → "VIP-Platform: Committed `vendor/`" for the full rationale.

---

## Cross-skill References

- **Application-level security** (OWASP, nonces, capability checks, output escaping) → `web-security` skill + [`security.md`](security.md)
- **Performance** (object cache, remote requests, query optimization) → [`vip-performance.md`](vip-performance.md)
- **Plugin structure and scaffolder** → [`structure-and-scaffolding.md`](structure-and-scaffolding.md)

---

## Sources

- VIPCS (automattic/vipwpcs): https://github.com/Automattic/VIP-Coding-Standards
- WordPress VIP developer docs: https://docs.wpvip.com/
- VIP Composer guide: https://docs.wpvip.com/technical-references/vip-codebase/composer/
- WordPress Coding Standards (WPCS): https://github.com/WordPress/WordPress-Coding-Standards
