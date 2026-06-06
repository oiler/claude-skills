# Semantic Correctness — base layer (MDN)

> The base layer. The authority is MDN / the HTML Living Standard. This layer is enforced in **every** mode and **every** authority level — FEE never ships semantically broken markup. The style layer (markup-style.md) only chooses among options this layer considers valid.

**Captured:** MDN / HTML Living Standard, captured 2026-06-06.
**Escape hatch:** for an element or attribute not covered here, fetch the relevant MDN page at write-time rather than guessing.

## Precedence
1. Correctness (this layer) always wins over the style layer.
2. If oiler explicitly requests something semantically off, build it but flag the divergence and why.
3. Never silently emit incorrect markup.

## Sectioning & landmarks
- One `<main>` per page; do not nest it in `article`/`aside`/`header`/`footer`/`nav`. (MDN: Element/main)
- `<section>` needs a heading and a thematic grouping; default to `<div>` for non-semantic grouping. (MDN: Element/section)
- A wrapper whose only job is grouping repeated `<article>`s is non-semantic — use `<div>`, or, if a landmark is wanted, give the `<section>` its own accessible name via `aria-label`/`aria-labelledby` (a `<section>`'s name comes from its own heading, not its children's). (MDN: Element/section)
- `<article>` for independently distributable content; `<section>` for a thematic chunk of one document. (MDN: Element/article)
- `<nav>` for major navigation blocks, not every group of links. (MDN: Element/nav)
- `<header>`/`<footer>` are scoped to their nearest sectioning ancestor. (MDN: Element/header)
- `<aside>` for content tangential to the surrounding content. (MDN: Element/aside)

## Headings
- One logical `<h1>` per page; do not skip heading levels for styling. (MDN: Element/Heading_Elements)
- Heading level reflects document-outline depth, not font size. (MDN: Element/Heading_Elements)

## ARIA
- First rule of ARIA: prefer a native element with built-in semantics over a `role`. No ARIA is better than bad ARIA. (MDN: Web/Accessibility/ARIA)
- Do not set a `role` that duplicates an element's implicit role (e.g. `role="main"` on `<main>`). (MDN: Web/Accessibility/ARIA/Roles)
- Interactive widgets (tabs, dialog, menu) need the full required states/relationships, not just `role`. (MDN: Web/Accessibility/ARIA/Roles/tab_role)
- `aria-labelledby`/`aria-controls` must reference IDs that actually exist on the page. (MDN: Web/Accessibility/ARIA/Attributes/aria-labelledby)
- Any element with a non-native interactive `role` must be keyboard operable (focusable + key handlers). (MDN: Web/Accessibility/ARIA/Roles)

## Forms
- Every control has a programmatic label (`<label for>` or wrapping the control). (MDN: Element/label)
- Group related controls with `<fieldset>`/`<legend>`. (MDN: Element/fieldset)
- Use the correct `input[type]` and `autocomplete` tokens for the data. (MDN: Element/input)
- A `<button>` inside a form defaults to `type="submit"`; set `type="button"` for non-submitting buttons. (MDN: Element/button)

## Lists & tables
- `<ul>`/`<ol>` may directly contain only `<li>` (plus script-supporting elements). (MDN: Element/ul)
- `<dl>` pairs `<dt>`/`<dd>` for name/value groups. (MDN: Element/dl)
- Data tables use `<th scope>` and a `<caption>`; never use tables for layout. (MDN: Element/table)

## Media
- Content `<img>` requires meaningful `alt`; decorative images use `alt=""`. (MDN: Element/img)
- Set explicit `width`/`height` (or CSS aspect-ratio) to prevent layout shift; use `loading="lazy"` for below-the-fold images and `srcset`/`sizes` for responsive images. (MDN: Element/img, Web/Performance/Lazy_loading)
- Do NOT `loading="lazy"` an above-the-fold / LCP image — it delays the largest contentful paint; use `loading="eager"` or omit `loading`, and reserve lazy for below-the-fold images. (MDN: Web/Performance/Lazy_loading)
- Provide captions/subtitles for `<video>`/`<audio>` via `<track>` where applicable. (MDN: Element/track)

## Document
- Set `<html lang>`; provide exactly one `<title>`; include `<meta charset="utf-8">` and a responsive `<meta name="viewport">`. (MDN: Element/html, Element/meta/name/viewport)
- Use `<a>` for navigation and `<button>` for actions — never a clickable `<div>`. (MDN: Element/a, Element/button)
