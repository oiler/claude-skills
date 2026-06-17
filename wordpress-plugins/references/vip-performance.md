# VIP Performance at Scale

Performance rules for WordPress plugins targeting WordPress VIP. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025), VIPCS 3.0+.

---

## Object Cache

Use `wp_cache_get` / `wp_cache_set` / `wp_cache_delete` with a plugin-specific **cache group** and an explicit **TTL** (seconds). The group namespaces your keys to avoid collisions with core or other plugins; the TTL prevents stale data from persisting indefinitely.

> **VIP-Platform:** The object cache is persistent (Memcached/Redis-backed). Cache set in one request is available to the next. Self-hosted installs without a persistent object-cache drop-in use a per-request in-memory store — a cache miss on every request is the default, not the exception.

```php
$cache_key   = 'event_count_' . $event_id;
$cache_group = 'my_plugin';
$ttl         = 5 * MINUTE_IN_SECONDS; // Why: event counts are cheap to recompute; 5 min is stale enough to avoid redundant queries without serving stale counts for long.

$count = wp_cache_get( $cache_key, $cache_group );

if ( false === $count ) {
    $count = expensive_count_query( $event_id );
    wp_cache_set( $cache_key, $count, $cache_group, $ttl );
}

// To invalidate on write:
wp_cache_delete( $cache_key, $cache_group );
```

---

## Transients vs Object Cache

Use **transients** (`get_transient` / `set_transient`) for expensive computed values that need a persistent expiry you can rely on even without a persistent object-cache drop-in (e.g., aggregated stats, external feed results).

Use the **object cache directly** for hot per-request lookups where a persistent layer is guaranteed (VIP) or where a per-request cache is sufficient.

> **VIP-Platform:** Transients are backed by the persistent object cache; `set_transient` maps to `wp_cache_set` and the `wp_options` `_transient_*` row is bypassed entirely. On self-hosted sites without a persistent cache drop-in, transients fall back to `wp_options` — a database write per set.

```php
// Transient — suitable for expensive computed values or external data with a meaningful TTL.
$data = get_transient( 'my_plugin_feed_items' );

if ( false === $data ) {
    $data = fetch_external_feed(); // slow operation
    set_transient( 'my_plugin_feed_items', $data, HOUR_IN_SECONDS );
}

// Object cache — suitable for hot per-request lookups on VIP.
$meta = wp_cache_get( 'user_prefs_' . $user_id, 'my_plugin' );

if ( false === $meta ) {
    $meta = compute_user_prefs( $user_id );
    wp_cache_set( 'user_prefs_' . $user_id, $meta, 'my_plugin', 2 * MINUTE_IN_SECONDS );
}
```

---

## Mandatory Remote-Call Caching

Every `wp_remote_get`, `wp_remote_post`, and `wp_oembed_get` call **must** be wrapped in a cache layer (object cache or transient) with a sane TTL. Uncached remote calls block the PHP process for the full request duration on every page load and cause cascading timeouts under traffic.

Always pass a `timeout` argument. Always use the WP HTTP API — never raw `curl_exec`.

```php
function my_plugin_fetch_api_data( string $endpoint ): array|false {
    $cache_key   = 'api_' . md5( $endpoint );
    $cache_group = 'my_plugin_remote';

    $cached = wp_cache_get( $cache_key, $cache_group, false, $found );
    if ( $found ) {
        return $cached;
    }

    $response = wp_remote_get(
        $endpoint,
        [
            'timeout' => 5, // Why: 5 s is generous for internal APIs; keeps requests from blocking page renders.
            'headers' => [ 'Accept' => 'application/json' ],
        ]
    );

    if ( is_wp_error( $response ) || 200 !== wp_remote_retrieve_response_code( $response ) ) {
        // Cache a negative result briefly to avoid hammering a failing endpoint.
        wp_cache_set( $cache_key, false, $cache_group, 30 );
        return false;
    }

    $data = json_decode( wp_remote_retrieve_body( $response ), true );
    wp_cache_set( $cache_key, $data, $cache_group, 15 * MINUTE_IN_SECONDS );

    return $data;
}
```

---

## Bounded Queries

Never pass `'posts_per_page' => -1` or `'nopaging' => true`. On a site with thousands of posts this loads every matching row into PHP memory in a single query, exhausting memory and saturating the database. Always use a numeric cap and paginate batch work across multiple requests or cron ticks.

```php
$page = 1;
$args = [
    'post_type'      => 'event',
    'post_status'    => 'publish',
    'posts_per_page' => 100,
    'paged'          => $page,
    'no_found_rows'  => true, // Why: skip COUNT(*) in batch loops; no pagination UI needed.
];

$query = new WP_Query( $args );
// Process $query->posts, increment $page, repeat until posts is empty.
```

> **Offset vs. keyset:** The cron batch example below uses `offset`-based pagination, which is simple but degrades on large offsets — the database still scans all skipped rows. For large batch jobs, prefer `paged`-based iteration (as above) or process by ascending ID range (`'post__in'` / `WHERE ID > $last_id`) to let the index seek directly to the next chunk.

---

## `WP_Query` Over `get_posts()`

Prefer `WP_Query` for control and explicitness. Always declare `'post_type'` and `'post_status'` — never rely on defaults, which change across WordPress versions. Set `'no_found_rows' => true` to skip the `COUNT(*)` query when you have no pagination UI. Set `'update_post_meta_cache'` / `'update_post_term_cache'` to `false` when you will not access meta or terms in the loop — avoids extra `WHERE post_id IN (...)` queries.

```php
$query = new WP_Query(
    [
        'post_type'              => 'event',           // explicit — never rely on default
        'post_status'            => 'publish',         // explicit
        'posts_per_page'         => 50,
        'no_found_rows'          => true,              // Why: no pagination UI needed here.
        'update_post_meta_cache' => false,             // Why: loop only reads post title; meta unused.
        'update_post_term_cache' => false,             // Why: no taxonomy display in this loop.
    ]
);
```

`get_posts()` sets `suppress_filters => true` by default, which breaks some caching layers. Reserve it for simple one-off lookups where brevity is intentional and the defaults are acceptable.

---

## Avoid `post__not_in`

`post__not_in` appends `WHERE post_id NOT IN (...)` — never covered by the standard `wp_posts` indexes, forces a full-index scan on large tables, and degrades VIP cache-hit rate because the SQL string varies with the exclusion set. Filter unwanted IDs in PHP instead.

```php
// Prefer — fetch a slightly larger set, then filter in PHP.
$args = [
    'post_type'      => 'product',
    'post_status'    => 'publish',
    'posts_per_page' => 50 + count( $excluded_ids ), // extra rows compensate for PHP-side filtering
    'no_found_rows'  => true,
];

$query   = new WP_Query( $args );
$exclude = array_flip( $excluded_ids );
$posts   = array_filter(
    $query->posts,
    static fn( \WP_Post $p ) => ! isset( $exclude[ $p->ID ] )
);
$posts   = array_slice( $posts, 0, 50 );
```

---

## Taxonomy Queries

Set `'include_children' => false` in every `tax_query` entry unless you explicitly need descendant-term matching. `include_children` defaults to `true`, which causes an expensive recursive query to expand all child terms before the main query runs. On a deep term hierarchy this adds a substantial latency multiplier.

```php
$query = new WP_Query(
    [
        'post_type'   => 'event',
        'post_status' => 'publish',
        'tax_query'   => [
            [
                'taxonomy'         => 'event_category',
                'field'            => 'term_id',
                'terms'            => [ 42 ],
                'include_children' => false, // Why: we want exactly this term, not its descendants; avoids recursive expansion.
            ],
        ],
    ]
);
```

---

## Meta Queries

`meta_value` in `wp_postmeta` is not indexed. A `meta_key = 'foo' AND meta_value = 'bar'` query uses the `meta_key` index but scans every matching row to compare `meta_value`. `LIKE '%…%'` on `meta_value` is always a full-table scan.

- **Avoid `LIKE` on `meta_value`** — move substring-searchable data to a custom table or a search index (e.g., Elasticsearch on VIP).
- **Use a taxonomy for high-cardinality filtering** (status flags, categories) — term relationships are indexed.
- **Prefer `EXISTS` / `NOT EXISTS`** over value comparisons when only testing presence.
- **Custom DB indexes** require a VIP-platform conversation — raise with the VIP team when restructuring cannot fix the query.

```php
// Avoid — unindexed meta_value scan.
$args = [ 'meta_query' => [ [ 'key' => 'event_status', 'value' => 'active', 'compare' => '=' ] ] ];

// Prefer — taxonomy term relationships are indexed.
$args = [
    'tax_query' => [
        [ 'taxonomy' => 'event_status', 'field' => 'slug', 'terms' => [ 'active' ], 'include_children' => false ],
    ],
];

// Acceptable — key-existence check uses the meta_key index.
$args = [ 'meta_query' => [ [ 'key' => '_featured_override', 'compare' => 'EXISTS' ] ] ];
```

---

## Cron and Batch at Scale

Never perform heavy work synchronously on a page request — database migrations, bulk post updates, external API ingestion. Offload to `wp_schedule_single_event` (one-time) or `wp_schedule_event` (recurring).

Process in bounded chunks (≤ 100 items per tick) and re-schedule the next chunk if work remains. This keeps each cron execution within PHP's memory and time limits and avoids locking rows for long periods.

> **VIP-Platform:** WP-Cron is driven by the platform's system cron — it fires on a regular schedule independent of page loads. Self-hosted sites without a system cron entry depend on WP's default behavior of firing cron on page load, which means low-traffic sites may miss scheduled events.

```php
// ── One-time batch: schedule first chunk on activation ──────────────────────
register_activation_hook( __FILE__, static function (): void {
    if ( ! wp_next_scheduled( 'my_plugin_process_batch' ) ) {
        wp_schedule_single_event( time(), 'my_plugin_process_batch', [ 0 ] );
    }
} );
add_action( 'my_plugin_process_batch', static function ( int $offset ): void {
    $chunk_size = 100; // Why: bounded chunk keeps memory and query time predictable.

    $query = new WP_Query(
        [
            'post_type'              => 'event',
            'post_status'            => 'publish',
            'posts_per_page'         => $chunk_size,
            'offset'                 => $offset,
            'no_found_rows'          => true,  // Why: batch loop; no pagination UI needed.
            'update_post_meta_cache' => false,
            'update_post_term_cache' => false,
        ]
    );

    if ( empty( $query->posts ) ) {
        return; // All chunks processed.
    }

    foreach ( $query->posts as $post ) {
        process_single_event( $post );
    }

    // Re-schedule next chunk; 30 s gap avoids back-to-back DB saturation.
    wp_schedule_single_event( time() + 30, 'my_plugin_process_batch', [ $offset + $chunk_size ] );
} );
// ── Recurring task ───────────────────────────────────────────────────────────
add_filter( 'cron_schedules', static function ( array $schedules ): array {
    $schedules['every_15_minutes'] = [
        'interval' => 15 * MINUTE_IN_SECONDS,
        'display'  => 'Every 15 Minutes',
    ];
    return $schedules;
} );

register_activation_hook( __FILE__, static function (): void {
    if ( ! wp_next_scheduled( 'my_plugin_sync' ) ) {
        wp_schedule_event( time(), 'every_15_minutes', 'my_plugin_sync' );
    }
} );

register_deactivation_hook( __FILE__, static function (): void {
    wp_clear_scheduled_hook( 'my_plugin_sync' ); // Always clear on deactivation.
} );
```

---

## Cross-skill References

- **Security** — input validation, nonce verification, capability checks, and output escaping are in `security.md` (this skill's sibling). Web application security concerns route to the `web-security` skill.
- **Plugin structure** — activation/deactivation hook placement, singleton bootstrap, and `uninstall.php` are in `structure-and-scaffolding.md`.
