# Markup Style Layer — oiler

> oiler's personal HTML conventions. This is the **style layer** — it operates only within what the base layer (semantic-html.md) considers correct. Flexes with authority mode (see SKILL.md). Extracted from authored samples; re-extract when new authored markup is added.

**Extracted:** 2026-06-06 — from foxlaboratory.com `<body>` and baseballprospectus.com `.container`.

## Indentation & whitespace
- Tabs for indentation (canonical). (sample: foxlaboratory L83–L104)
- Blank lines separate major structural blocks, e.g. between `</header>` and `<main>`, and between sibling `<section>`s. (sample: foxlaboratory L105–L108; bp L368–L372)

## Document structure & landmarks
- `<header>`, `<nav>`, `<main>`, `<footer>` used as top-level landmark elements wrapping the page. (sample: foxlaboratory L83, L90, L108, L143)
- `<section>` used for named, thematic content groupings within a page region. (sample: bp L313, L372, L424, L474)

## Class naming
- Site-scoped prefix on owned structural components: `fdl-header`, `fdl-nav`, `fdl-text-logo`, `fdl-details`, `fdl-page-content`. (sample: foxlaboratory L83, L84, L90, L97, L108)
- BEM-like double-dash modifier for widget sub-elements: `<widget>--tabs`, `<widget>--entry`, `<widget>--entry-container`, `<widget>--entry-content`. (sample: bp L477, L484, L485, L486)
- Flat hyphen-separated multi-word classes for layout/content zones: `hp-top`, `hp-bottom`, `box-label`. (sample: bp L313, L372, L512)
- `is-active` state class on the active item in a stateful widget. (sample: bp L478, L484)

## IDs
- IDs for landmark anchoring and JS targeting: `id="site-content"`, `id="sidebar-primary"`. (sample: foxlaboratory L108, L138)
- Widget panel IDs follow `<group>__<slug>`: `recent_articles__features`, `recent_articles__prospects`. (sample: bp L484, L491)
- Widget trigger IDs follow `<thing>_<slug>`: `tab_features`, `tab_prospects`. (sample: bp L478, L479)

## ARIA & interactive widgets
- Custom (non-native) interactive widgets get full ARIA wiring, not just a role. Tab container: `role="tablist"` + `aria-label`. (sample: bp L477, L516)
- Each tab trigger: `role="tab"` + `aria-selected="true|false"` + `aria-controls` → its panel ID. (sample: bp L478–L481)
- Inactive triggers get `tabindex="-1"`; the active trigger omits `tabindex`. (sample: bp L478–L481)
- Tab panels: `role="tabpanel"` + `tabindex="0"`, with `aria-labelledby` → the real trigger `id`. (Note: the sample's `aria-labelledby` uses generic ordinals `tab1`/`tab2` that don't match the actual IDs — an apparent bug; the base layer requires the real `id`.) (sample: bp L484, L478)
- Do NOT add a `role` that merely duplicates a native element's implicit role (e.g. no `role="main"` on `<main>`) — defer to the base layer.

## Comments
- Commented-out markup preserved in place as toggle markers rather than deleted. (sample: foxlaboratory L109, L112, L144)
- Short descriptive labels as section comments ahead of widget blocks: `<!-- front box recent articles -->`. (sample: bp L475, L514)
- Larger commented-out functional blocks kept multi-line, indented to match surroundings. (sample: bp L525–L527)

## Links & navigation
- Nav link text is all-lowercase: "home", "about", "work", "notes", "contact". (sample: foxlaboratory L91–L95)
- Active/current nav link marked with `class="current"`. (sample: foxlaboratory L91)

## Images
- Decorative/context images use empty `alt=""`; branded logos use descriptive alt text. (sample: bp L317; foxlaboratory L86)
- Content images carry explicit `width` + `height`, `loading="lazy"`, `srcset`, and `sizes`. (sample: bp L317, L330)
- Logo/header images carry explicit `width` only (no height/lazy/srcset). (sample: foxlaboratory L86–L87)
- Attribute order on content `<img>`: `width`, `height`, `src`, `class`, `alt`, `loading`, `srcset`, `sizes`. (sample: bp L317)

## Attribute ordering
- On a structural `<div>` with a data hook: `class`, then `data-*`. (sample: bp L476)
- On a custom tab trigger: `class`, `role`, `aria-selected`, `aria-controls`, `id`, then `tabindex` only when inactive. (sample: bp L478–L481)
- On a tab panel: `id`, `class`, `data-title`, `tabindex`, `role`, `aria-labelledby`. (sample: bp L484, L491)

## Document-level
- No clear convention observed in authored regions (`<html lang>` and `<head>` are framework-generated and were excluded).

## Tentative (seen once — confirm before promoting)
- `<h6>` used as a tab trigger element (not a heading-hierarchy choice) — seen once. (sample: bp L478–L481)
- Trailing whitespace before `>` on classless nav links: `<a href="/about" >about</a>` — likely an artifact, not a convention. (sample: foxlaboratory L92–L95)
