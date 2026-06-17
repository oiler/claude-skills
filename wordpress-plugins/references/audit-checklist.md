# Plugin Audit Checklist

Graded checklist for auditing an existing WordPress plugin against VIP standards. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025) / VIPCS 3.0+.

---

## How to Run an Audit

1. **Read the plugin.** Walk the directory top-down: main plugin file, `src/`, templates, any REST route registrations, AJAX handlers, and `uninstall.php`.
2. **Run the linter** if the project has `composer.json` with `vipwpcs`:
   ```bash
   composer lint   # phpcs — flags VIPCS violations; review the full output before continuing
   ```
   PHPCS catches many items below automatically. Work through remaining items manually.
3. **Walk the checklist below.** Grep hints are provided per item — run them from the plugin root.
4. **Produce the report.** Fill the template at the end. Group findings as **Errors** (platform-blocking) or **Advisories** (quality/style).

---

## Error Taxonomy — VIP-Platform-Blocking

A plugin with any open Error cannot ship to WordPress VIP Go.

### E1 — Unbounded Query

**Grep:** `grep -rn "posts_per_page.*-1\|'nopaging'.*true" --include="*.php" .`

**What to look for:** `'posts_per_page' => -1` or `'nopaging' => true` in any `WP_Query`, `get_posts()`, or raw `query_posts()` argument array.

**Why it's blocking:** Loads every matching row into PHP memory in a single hit; exhausts memory allocations and saturates the shared database on VIP Platform.

**Fix:** Replace with a numeric cap (`'posts_per_page' => 100`) and paginate across multiple requests or cron ticks.

**Deep reference:** [`vip-performance.md`](vip-performance.md) → "Bounded Queries"

---

### E2 — Uncached Remote Call

**Grep:** `grep -rn "wp_remote_get\|wp_remote_post\|wp_remote_request\|wp_oembed_get" --include="*.php" .`

**What to look for:** Any `wp_remote_*` or `wp_oembed_get` call that is not wrapped in a `wp_cache_get` / `get_transient` guard. Look for the pattern: the remote call appears without a preceding cache-check conditional.

**Why it's blocking:** Blocks the PHP process for the full network round-trip on every page load; causes cascading timeouts under traffic. VIP Platform has strict per-request time budgets.

**Fix:** Wrap every remote call in a cache layer (`wp_cache_get` / `wp_cache_set` or `get_transient` / `set_transient`) with a sane TTL. Always pass `'timeout'` in the request args.

**Deep reference:** [`vip-performance.md`](vip-performance.md) → "Mandatory Remote-Call Caching"

---

### E3 — Direct Filesystem Write

**Grep:** `grep -rn "file_put_contents\|fopen\|fwrite\|unlink\|mkdir\|rmdir" --include="*.php" .`

**What to look for:** Direct PHP filesystem functions used for writing or deleting files.

**Why it's blocking:** VIP Platform filesystem is read-only outside `wp-content/uploads`; direct writes fail at runtime. Bypassing the WP Filesystem API also breaks FTP/SSH transport environments on self-hosted sites.

**Fix:** Use `WP_Filesystem()` + `$wp_filesystem->put_contents()` for writes. Use `wp_upload_dir()` to resolve the writable uploads path. For uploaded files, use `wp_handle_upload()`.

**Deep reference:** [`vip-standards.md`](vip-standards.md) → "Direct Filesystem Writes"

---

### E4 — Missing or Unverified Nonce on State-Changing Action

**Grep:** `grep -rn "admin_post_\|wp_ajax_\|action.*save\|action.*update\|action.*delete" --include="*.php" .`

**What to look for:** Any `add_action` handler for `admin_post_*`, `wp_ajax_*`, or custom admin page submissions that does not call `check_admin_referer()`, `check_ajax_referer()`, or `wp_verify_nonce()` before processing `$_POST` / `$_GET` data.

**Why it's blocking:** Without nonce verification, state-changing actions are vulnerable to CSRF — an attacker can trick an authenticated admin into triggering arbitrary plugin actions. VIP reviewers treat this as a hard blocker.

**Fix:** Call `check_admin_referer( $action, $field )` in admin POST handlers, `check_ajax_referer( $action, $field )` in AJAX handlers, or `wp_verify_nonce( $nonce, $action )` in custom flows — before any data processing.

**Deep reference:** [`security.md`](security.md) → "Nonces — CSRF Protection for Forms and AJAX"

---

### E5 — Missing Capability Check

**Grep:** `grep -rn "admin_post_\|wp_ajax_\|register_rest_route" --include="*.php" .`

**What to look for:** Handlers that process requests without calling `current_user_can()` before acting. Also flag routes registered with `register_rest_route` that lack a meaningful `permission_callback`. Nonce checks (E4) are CSRF protection, not authorization — both are required.

**Why it's blocking:** Without a capability check, any authenticated (or unauthenticated) user can trigger privileged operations — deleting content, changing settings, reading private data. Critical privilege-escalation class.

**Fix:** Call `current_user_can( 'manage_options' )` (or the appropriate capability) immediately after the nonce check. For REST routes, provide a real `permission_callback` — see E8.

**Deep reference:** [`security.md`](security.md) → "Capability Checks — Authorization"

---

### E6 — Unescaped Output

**Grep:** `grep -rn "echo \$\|echo get_\|echo esc_\b" --include="*.php" . | grep -v "esc_html\|esc_attr\|esc_url\|esc_js\|esc_textarea\|wp_kses"` (review manually — grep is a hint, not exhaustive)

**What to look for:** Any `echo` or `print` that outputs a variable or function return value without an `esc_*` / `wp_kses*` wrapper. Pay special attention to post meta, option values, user input, and URL parameters reflected into HTML.

**Why it's blocking:** Unescaped output is a stored or reflected XSS vector. On WordPress VIP, which hosts high-value sites, XSS is treated as a critical security vulnerability.

**Fix:** Escape at the output site using the context-appropriate function: `esc_html()`, `esc_attr()`, `esc_url()`, `esc_js()`, `wp_kses_post()`, or `wp_kses()`. For translated strings, use the combo helpers (`esc_html_e()`, `esc_attr__()`).

**Deep reference:** [`security.md`](security.md) → "Escape at Output (Late Escaping)"

---

### E7 — Unprepared `$wpdb` SQL

**Grep:** `grep -rn "\$wpdb->" --include="*.php" .`

**What to look for:** `$wpdb->query()`, `$wpdb->get_results()`, `$wpdb->get_var()`, etc. where the SQL string is built by string concatenation or interpolation rather than `$wpdb->prepare()`. Look for `"SELECT ... WHERE ... = '" . $var . "'"` or `"... = {$var}"` patterns.

**Why it's blocking:** Unprepared SQL is a SQL injection vulnerability. It is always blocking on VIP and flagged by VIPCS.

**Fix:** Use `$wpdb->prepare( $sql, ...$args )` with typed placeholders (`%d`, `%s`, `%f`, `%i` for identifiers). Prefer core API functions (`WP_Query`, `get_post_meta`, etc.) over raw SQL when possible.

**Deep reference:** [`security.md`](security.md) → "Prepared Statements (`$wpdb`)" and [`vip-standards.md`](vip-standards.md) → "Direct Database Access"

---

### E8 — `register_rest_route` with `__return_true` on Write Routes

**Grep:** `grep -rn "permission_callback.*__return_true\|__return_true.*permission_callback" --include="*.php" .`

**What to look for:** Any `register_rest_route()` call that uses `'permission_callback' => '__return_true'` (or an equivalent always-true closure) on a route that accepts `POST`, `PUT`, `PATCH`, or `DELETE` methods, or that returns private data on `GET`.

**Why it's blocking:** `__return_true` grants any request — including unauthenticated — full access to the route. Write routes without authorization are a data integrity and privilege-escalation vulnerability.

**Fix:** Replace with a real callback: `'permission_callback' => fn() => current_user_can( 'manage_options' )` (or the appropriate capability). Read-only public data routes may use `__return_true` intentionally — confirm intent before flagging.

**Deep reference:** [`security.md`](security.md) → "REST API — `register_rest_route`"

---

### E9 — `eval()` / `create_function()`

**Grep:** `grep -rn "\beval\b\|create_function" --include="*.php" .`

**What to look for:** Any call to `eval()` or `create_function()`, regardless of whether the argument appears to be hard-coded.

**Why it's blocking:** These functions execute arbitrary PHP. There is no safe form. VIPCS flags both as errors; VIP platform review will reject any plugin containing them.

**Fix:** Refactor to a named function or closure. `create_function` is also deprecated as of PHP 7.2 and removed in PHP 8.0.

**Deep reference:** [`vip-standards.md`](vip-standards.md) → "Dynamic Code Execution"

---

### E10 — Hardcoded Paths or URLs

**Grep:** `grep -rn "\/var\/www\|\/home\/\|\/srv\/\|http:\/\/\|https:\/\/" --include="*.php" . | grep -v "license\|License\|@link\|@see\|readme\|\.org"`

**What to look for:** Hardcoded absolute filesystem paths (anything starting with `/` that is not a constant like `ABSPATH` or `WP_CONTENT_DIR`) or hardcoded domain URLs embedded in plugin logic. Also flag `/tmp` used as a reliable writable path.

**Why it's blocking:** Hardcoded paths break on VIP Platform and any environment that doesn't match the dev machine. Hardcoded URLs break multisite, staging/production parity, and HTTPS migrations.

**Fix:** Use WordPress constants (`ABSPATH`, `WP_CONTENT_DIR`, `WP_PLUGIN_DIR`) and functions (`plugin_dir_path()`, `plugin_dir_url()`, `wp_upload_dir()`, `home_url()`, `admin_url()`) for all path and URL resolution.

**Deep reference:** [`structure-and-scaffolding.md`](structure-and-scaffolding.md) → "Main Plugin File" and [`vip-standards.md`](vip-standards.md) → "Read-only Filesystem"

---

## Advisory Taxonomy

Advisories are quality and style issues — not platform-blocking on VIP, but expected to be addressed before shipping. On a self-hosted plugin these are best practices, not hard requirements.

### A1 — Missing PHPDoc

**What to look for:** Classes and public/protected methods without a `/** ... */` docblock. Also flag missing file-level `@package`. Private methods without obvious intent are worth flagging too.

**Deep reference:** [`documentation.md`](documentation.md) → "PHPDoc"

---

### A2 — `readme.txt` `Stable tag` Drift from Plugin Header `Version`

**Check:** Compare `Stable tag:` in `readme.txt` with `Version:` in the main plugin file header. Any mismatch is a finding.

**Deep reference:** [`documentation.md`](documentation.md) → "`readme.txt`" → "Header fields"

---

### A3 — Missing `@since` Tag

**What to look for:** For each docblock that contains `@param` or `@return`, confirm a sibling `@since` line is present in the same docblock. A single `grep` cannot detect a missing tag across docblock lines — rely on `composer lint` with the `WordPress-Docs` standard, which flags this automatically. Review lint output rather than grep output for this item.

**Deep reference:** [`documentation.md`](documentation.md) → "`@since` discipline"

---

### A4 — Non-PSR-4 Class Placement

**Check:** For each class file under `src/`, verify the namespace maps to its path per the `composer.json` autoload map. Example: `My_Plugin\CPT\Event` → `src/CPT/Event.php`. Flag classes in the plugin root or with mismatched filenames.

**Deep reference:** [`structure-and-scaffolding.md`](structure-and-scaffolding.md) → "OOP + PSR-4"

---

### A5 — Missing Text Domain on i18n Calls

**Grep:** `grep -rn "__(\|_e(\|esc_html__(\|esc_html_e(\|_n(\|_x(" --include="*.php" . | grep -v "'my-plugin'"` (replace `my-plugin` with the plugin's actual text domain)

**What to look for:** Any `__()`, `_e()`, `_n()`, `_x()`, or their `esc_*` variants called without a text domain argument, or with a hardcoded domain that does not match the plugin's registered `Text Domain`.

**Deep reference:** [`vip-standards.md`](vip-standards.md) → "Ruleset Overview" (the `WordPress.WP.I18n` rule in `phpcs.xml.dist`)

---

### A6 — Comment-the-Obvious Noise

**What to look for:** Inline comments that restate what the code already says (e.g., `// Flush rewrite rules.` above `flush_rewrite_rules()`). Also flag removed-code comments and unattributed TODO/FIXME entries.

**Why it matters:** Noise comments get stale, mislead future readers, and obscure the rare comment that explains *why*.

**Deep reference:** [`documentation.md`](documentation.md) → "Inline Comments"

---

## Report Template

Fill this skeleton for each plugin audit. Remove sections with no findings.
```markdown
# Plugin Audit: <Plugin Name> <Version>

Auditor: <name>  
Date: <YYYY-MM-DD>  
Scope: <plugin root path or repo>  
Linter: `composer lint` run: yes / no / not configured

---

## Summary

| Category  | Count |
|-----------|-------|
| Errors    | N     |
| Advisories| N     |

Overall: PASS / FAIL (Errors = 0 required to PASS)

---

## Errors

### [E1] Unbounded Query — `src/Import/Batch.php:47`

**Severity:** Error  
**Rule:** Bounded Queries ([`vip-performance.md`](vip-performance.md))  
**Finding:** `'posts_per_page' => -1` in `WP_Query` args — will load all posts into memory.  
**Fix:** Replace with `'posts_per_page' => 100` and paginate across cron ticks.

<!-- Repeat per Error finding -->

---

## Advisories

### [A1] Missing PHPDoc — `src/Settings.php:23`

**Severity:** Advisory  
**Rule:** PHPDoc ([`documentation.md`](documentation.md))  
**Finding:** `register_settings_page()` has no docblock.  
**Fix:** Add a summary docblock with `@since` and `@return void`.

<!-- Repeat per Advisory finding -->
```

---

## Cross-skill References

- **Performance rules** (bounded queries, remote-call caching, object cache, `post__not_in`) → [`vip-performance.md`](vip-performance.md)
- **VIPCS ruleset, restricted functions, platform constraints** → [`vip-standards.md`](vip-standards.md)
- **Security APIs** (nonces, capabilities, escaping, prepared statements, REST) → [`security.md`](security.md)
- **Structure, PSR-4, plugin scaffolding** → [`structure-and-scaffolding.md`](structure-and-scaffolding.md)
- **PHPDoc, `readme.txt`, inline comments** → [`documentation.md`](documentation.md)
- **Application-security fundamentals** (OWASP, XSS/CSRF/injection theory) → `web-security` skill
