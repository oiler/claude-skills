# Testing guards: what WordPress calls actually fold

Recognizing which WordPress calls fold several conditions into one outcome, so mutations can be written one per condition. Targets: WordPress 6.x, PHP 8.1+, VIP Coding Standards (2025). Every core claim below was verified by reading core; the line numbers are from WordPress 7.0.2 and drift between branches, so treat them as pointers and re-check the surrounding code rather than the line.

A guard that folds several conditions into one outcome cannot be pinned by a test that only observes the outcome. Deleting the whole call proves the guard exists; removing one condition proves which test depends on it. These are the WordPress calls where that matters most.

## `get_edit_post_link( $id )`

Returns null for **three** independent reasons (`wp-includes/link-template.php:1452-1486`):

1. the post does not exist (`! $post`),
2. the post type is not registered (`! $post_type_object`),
3. the current user fails `current_user_can( 'edit_post', $post->ID )`.

It does **not** check post status. A trashed post still yields an edit link.

There is deliberately no fourth condition for "the post type has no edit UI", and core's own docblock will tempt you to add one. `link-template.php:1449-1450` documents the return as "Null if the post type does not exist **or does not allow an editing UI**" — the second clause is wrong, and the code is what to follow. `show_ui` is genuinely the mechanism at work: `class-wp-post-type.php:623-624` empties `_edit_link` exactly when `! $args['show_ui'] && ! $has_edit_link`. But an empty `_edit_link` on a *registered* post type takes no branch at `link-template.php:1479-1486`, so `$link` keeps the `''` it was initialized to at `:1477` and `:1498` returns that empty string. `''`, not null. A caller testing `if ( $link )` conflates the two outcomes; one testing `null !== $link` distinguishes them, and only the second can tell a missing post type from a UI-less one.

That status point is not trivia. A reviewer once mutated away an explicit `isset( $subjects[ $id ] ) || current_user_can( 'edit_post', $id )` guard sitting directly above a `get_edit_post_link()` call, watched the suite stay green, and concluded the guard was fully shadowed and therefore redundant. The conclusion was wrong: a trashed source is absent from the subject list while `get_edit_post_link()` alone still emits an editor link to it. The guard was load-bearing on the trash path, and the corrected mutation exposed a real defect — an `action=edit` link to a trashed post.

Earlier, on a different build, the same function shadowed *the plugin's own post-type guard* — its own `if` on `$post->post_type`, not core's registered-type check in condition 2 above: a test passed the wrong post of a pair, the pair resolved backwards, the capability check failed first, and the plugin's post-type guard under test was never reached. The test asserted the right outcome through a mechanism unrelated to what it claimed to cover.

Same function, two builds, two different shadowing failures. Treat any `get_edit_post_link()` sitting near an explicit guard as a place where mutations must be per-condition.

## `current_user_can()` under `map_meta_cap`

`edit_post` and `edit_posts` are different guards, and swapping one for the other is the single most useful mutation on any capability check:

- `edit_posts` is a **primitive** capability. An author holds it.
- `edit_post` is a **meta** capability resolved per object (`wp-includes/capabilities.php:188`, inside `map_meta_cap()`). It requires a specific post as its argument and breaks down into `edit_posts`, `edit_published_posts`, or `edit_others_posts` depending on that post's author and status. An author does not hold it on another user's post.

A test that passes under both is not exercising the guard it names. Build the fixture so the two diverge: an author, and a post owned by someone else.

## `check_admin_referer()` and `check_ajax_referer()`

Both read the nonce from `$_REQUEST`, not `$_POST` (`wp-includes/pluggable.php:1379` and `:1424-1430`). (`wp_verify_nonce()` itself takes the nonce as an argument and reads no superglobal — the trap lives in the wrappers.) In a real request PHP populates `$_REQUEST` from `$_POST`, but under wp-phpunit the superglobals are set by hand and are not synced, so a test that populates only `$_POST` can pass without the nonce check ever being satisfied by the value the test thinks it set — or can fail for a reason unrelated to the guard. Set the value where the function actually reads it.

`check_admin_referer()` additionally dies on failure — `wp_nonce_ays()`, which ends in `wp_die()` (`functions.php:3727`), then `die()` — so a test asserting "nothing was written" may be observing the die rather than the guard under test. The die is conditional: `pluggable.php:1392` guards it with `! $result && ! ( -1 === $action && str_starts_with( $referer, $adminurl ) )`, so an invalid nonce with `$action === -1` and an admin referer returns false without dying. That is not a path plugin code should be on — it also trips `_doing_it_wrong()` at `:1374` — but a test relying on the die must pass a real action.

`check_ajax_referer()` also dies when its `$stop` argument is true (the default), but by a different route (`pluggable.php:1445-1451`): `wp_die( -1, 403 )` under `wp_doing_ajax()`, and a bare `die( '-1' )` otherwise. No `wp_nonce_ays()` is involved. `wp_doing_ajax()` is `defined( 'DOING_AJAX' ) && DOING_AJAX`, filterable (`load.php:1745-1754`), so outside `WP_Ajax_UnitTestCase` the bare `die()` is the branch taken — and a bare `die()` no `wp_die` handler can intercept. It terminates the PHPUnit process rather than throwing something a test can catch.

## Fetch-then-type-check on `get_post()`

Core `get_post( $id )` returns null only when the post does not exist — it has no type parameter. The fold happens in the caller: the common handler shape `$post = get_post( $id ); if ( ! $post || 'post' !== $post->post_type ) { return; }` collapses two conditions — missing post, wrong-type post — into one early return. Deleting the whole guard cannot tell you which of the two any given test pins; mutate each condition separately.

## Ordering hazards that produce green-for-the-wrong-reason

- Hook priority: a guard registered at priority 10 can pre-empt the guard under test, so the test observes the wrong gate entirely.
- Fixture order: once `register_setting()` has run — normally on `admin_init` — the sanitize callback is attached as a `sanitize_option_{$option_name}` filter (`option.php:3070-3072`), so every later `update_option()` in that test is sanitized. Fixtures planting deliberately-dirty state must be written **before** `admin_init`, or the setup itself routes through the callback and a broken contract silently discards it — producing a vacuous pass.
- `update_option()` on an option row that does not exist routes through `add_option()` and fires `add_option_{option}`, not `update_option_{option}`. An observer test written against the wrong hook cannot fail.

## The discipline

For each of the above, the mutation removes **one** condition and names **one** test that must go red. If no single test can be named, the test design is wrong — fix that before writing code.

A mutation that survives is not proof of equivalence. It is a question. Enumerate the input dimensions the equivalence claim covers — existence, status, type, capability, ordering, emptiness, multiplicity — and name what you excluded. If you cannot enumerate exhaustively, escalate.
