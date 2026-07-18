# Admin UI: List-Table Columns and the Settings API

Custom columns on post list tables (edit.php) and plugin settings pages via the Settings API. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025) / VIPCS 3.0+.

---

## Admin List-Table Columns

### The three-hook contract

A custom column needs up to three registrations. Registering only the first two produces the classic bug: the column renders everywhere but sorts nowhere (or worse, appears sortable on one post type and inert on another).

| Hook | Kind | Job |
|------|------|-----|
| `manage_{$post_type}_posts_columns` | filter | Add/remove/relabel columns — receives and returns the columns array |
| `manage_{$post_type}_posts_custom_column` | action | Render one cell — echoes the value for `($column_name, $post_id)` |
| `manage_edit-{$post_type}_sortable_columns` | filter | Declare which columns are sortable and what orderby value each maps to |

The sortable filter's shape differs from the other two because it derives from the screen id, not the post type: the core filter is `manage_{$screen->id}_sortable_columns`, and on `edit.php` the screen id is `edit-{$post_type}`. Writing `manage_{$post_type}_sortable_columns` (no `edit-`) registers a filter nothing ever fires — a silent failure.

```php
add_filter( 'manage_book_posts_columns', function ( array $columns ): array {
	$columns['book_isbn'] = __( 'ISBN', 'my-plugin' );
	return $columns;
} );

add_action( 'manage_book_posts_custom_column', function ( string $column_name, int $post_id ): void {
	if ( 'book_isbn' !== $column_name ) {
		return;
	}
	echo esc_html( (string) get_post_meta( $post_id, 'book_isbn', true ) );
}, 10, 2 );

add_filter( 'manage_edit-book_sortable_columns', function ( array $columns ): array {
	$columns['book_isbn'] = 'book_isbn'; // value becomes the orderby query arg
	return $columns;
} );
```

### Which hooks fire for which post types

**The `{$post_type}`-interpolated hooks are the universal per-post-type path** — they fire for every post type, hierarchical or not, and run after the generic hooks. Register those; they scope your column to exactly the post type it belongs to.

The generic hooks are the blanket-registration trap. Core's conditionals are asymmetric, which is why blanket registration produces bugs that differ between the filter and the render:

| Generic hook | Fires when |
|--------------|------------|
| `manage_posts_columns` / `manage_posts_custom_column` | All **non-hierarchical** post types |
| `manage_pages_columns` | **Only** `$post_type === 'page'` — not other hierarchical types |
| `manage_pages_custom_column` | **All hierarchical** post types |

Note the mismatch in the `pages` pair: the columns *filter* is page-only while the custom-column *action* is all-hierarchical. A plugin that adds a column via `manage_pages_columns` and renders via `manage_pages_custom_column` works on Pages but silently renders nothing (or renders into a column that was never added) on a hierarchical CPT. The fix is always the same: use the interpolated hooks per post type and loop over your supported types.

```php
foreach ( array( 'book', 'magazine' ) as $post_type ) {
	add_filter( "manage_{$post_type}_posts_columns", $add_columns );
	add_action( "manage_{$post_type}_posts_custom_column", $render_column, 10, 2 );
	add_filter( "manage_edit-{$post_type}_sortable_columns", $add_sortable );
}
```

### Sorting: when pre_get_posts is (and isn't) needed

Declaring a column sortable makes WordPress emit the orderby link. What happens on click depends on the orderby value you mapped:

- **Native orderby values** (`title`, `date`, `ID`, `comment_count`, `modified`, ...) — WP_Query understands them directly. No further code; adding a `pre_get_posts` handler for these is dead code.
- **Meta-backed or custom values** — WP_Query doesn't know what `book_isbn` means. Translate it in `pre_get_posts`, guarded so it only touches the admin list-table main query:

```php
add_action( 'pre_get_posts', function ( \WP_Query $query ): void {
	if ( ! is_admin() || ! $query->is_main_query() ) {
		return;
	}
	if ( 'book_isbn' !== $query->get( 'orderby' ) ) {
		return;
	}
	$query->set( 'meta_key', 'book_isbn' );
	$query->set( 'orderby', 'meta_value' );
} );
```

Use `meta_value_num` instead of `meta_value` for numeric meta, or the sort is lexicographic ("10" before "9").

> **VIP-Platform only.** Meta orderby runs an unindexed join against `wp_postmeta` by default. On large tables this is a slow query the platform will flag. Bound it: keep meta-sorted list tables paginated at the default per-page, and see [vip-performance.md](vip-performance.md) for the query-bounding rules before adding a meta sort to a post type with a large row count.

### Escaping in render callbacks

The custom-column action echoes directly into the admin table. Everything printed goes through the standard escaping discipline — `esc_html()` for text, `esc_attr()` inside attributes, `esc_url()` for links, `wp_kses_post()` only when markup is genuinely required. Post meta is user-supplied data no matter who wrote it. The full escaping rules and rationale live in [security.md](security.md) — this file doesn't restate them, it just reminds you the admin is not a trusted-output context.

### Audit signals

When auditing a plugin's admin columns, look for: generic-hook registration where interpolated hooks were intended (the `manage_pages_*` asymmetry above); a sortable filter using the wrong screen-id shape (missing `edit-`); `pre_get_posts` handlers without `is_admin()`/`is_main_query()` guards (they leak into front-end queries); unescaped `echo` in render callbacks; meta sorts on unbounded tables.

---

## Settings API

### Registration

Register every option with a sanitize callback. `register_setting()` without one stores raw `$_POST` data — the sanitize callback is the single choke point where option input becomes trusted, which is why it's non-negotiable rather than a style preference.

```php
add_action( 'admin_init', function (): void {
	register_setting(
		'my_plugin_settings',
		'my_plugin_options',
		array(
			'type'              => 'array',
			'sanitize_callback' => __NAMESPACE__ . '\\sanitize_options',
			'default'           => array( 'api_endpoint' => '' ),
		)
	);

	add_settings_section( 'my_plugin_main', __( 'Main Settings', 'my-plugin' ), '__return_null', 'my-plugin' );

	add_settings_field(
		'api_endpoint',
		__( 'API Endpoint', 'my-plugin' ),
		__NAMESPACE__ . '\\render_endpoint_field',
		'my-plugin',
		'my_plugin_main'
	);
} );

function sanitize_options( $input ): array {
	$clean                 = array();
	$clean['api_endpoint'] = isset( $input['api_endpoint'] ) ? esc_url_raw( (string) $input['api_endpoint'] ) : '';
	return $clean;
}
```

**Prefix option names yourself.** VIPCS's `PrefixAllGlobals` sniff checks functions, classes, global variables, constants, and hook names — it does **not** check option names passed to `register_setting()`/`update_option()`. An unprefixed option name (`options`, `settings`, `api_key`) collides silently with other plugins in the shared `wp_options` table, and no linter will tell you. Prefix with the plugin slug (`my_plugin_options`) as a convention this file carries because phpcs can't.

### The settings page

```php
add_action( 'admin_menu', function (): void {
	add_options_page(
		__( 'My Plugin', 'my-plugin' ),
		__( 'My Plugin', 'my-plugin' ),
		'manage_options',
		'my-plugin',
		__NAMESPACE__ . '\\render_settings_page'
	);
} );

function render_settings_page(): void {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html__( 'You do not have permission to access this page.', 'my-plugin' ) );
	}
	?>
	<div class="wrap">
		<h1><?php echo esc_html( get_admin_page_title() ); ?></h1>
		<form method="post" action="options.php">
			<?php
			settings_fields( 'my_plugin_settings' );   // nonce + option-group hidden fields
			do_settings_sections( 'my-plugin' );
			submit_button();
			?>
		</form>
	</div>
	<?php
}
```

Two layers of protection, and both matter: the capability check in the render callback controls who can *see* the page (the `add_options_page()` capability argument gates the menu entry, but re-checking in the callback costs nothing and survives refactors that expose the callback elsewhere); `settings_fields()` prints the nonce that `options.php` verifies on save — omit it and every save fails, roll your own form handler and you own nonce + capability verification manually. `manage_options` is the right default for site-level settings; scope narrower (a custom capability) when the settings are safe for non-admins to change, so you aren't handing full settings access to roles that only need one toggle.

### Output escaping

Escape stored options on output like any other data — `esc_url( $options['api_endpoint'] )` in an `href`, `esc_attr()` in a field's `value=""`. Sanitizing on input does not exempt output: the sanitize callback ran at save time under the rules of that plugin version, and the row may have been written by an older version, a migration, or WP-CLI. Escaping at output is the layer you control right now. Rationale and context-by-context rules: [security.md](security.md).

### VIP notes

> **VIP-Platform only.** `register_setting()`'s underlying `add_option()` autoloads by default — every autoloaded option ships on every request via `alloptions`, which on VIP is a flagged performance concern once options grow. For options read only on your settings screen or in a cron job, store with `autoload => false` (pass `'autoload' => false` in the `register_setting` args on WP 6.6+, or `update_option( $name, $value, false )`). Bounding rules and the `alloptions` failure mode: [vip-performance.md](vip-performance.md).

---

## Cross-references

- Escaping and capability discipline: [security.md](security.md)
- Query bounding, autoload, object cache: [vip-performance.md](vip-performance.md)
- Where admin-UI code lives in the plugin layout: [structure-and-scaffolding.md](structure-and-scaffolding.md)
