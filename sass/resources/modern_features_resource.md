# Modern CSS Features (2020-2025)

Features with widespread browser support that complement traditional CSS workflows.

## Container Queries

**Browser Support:** Chrome 105+, Safari 16+, Firefox 110+ (2023+)

Query parent container size instead of viewport:

```css
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card-title {
    font-size: 2rem;
  }
}
```

**Use cases:** Component-based responsive design, reusable components


## CSS Nesting (Native)

**Browser Support:** Chrome 112+, Safari 16.5+, Firefox 117+ (2023+)

Native nesting without Sass:

```css
.article {
  padding: 2rem;
  
  & .title {
    font-size: 2rem;
  }
  
  &:hover {
    background: #f5f5f5;
  }
}
```

**Note:** Can complement Sass nesting, not replace build process


## Cascade Layers (@layer)

**Browser Support:** Chrome 99+, Safari 15.4+, Firefox 97+ (2022+)

Control specificity with layers:

```css
@layer reset, base, components, utilities;

@layer reset {
  * { margin: 0; padding: 0; }
}

@layer components {
  .button { padding: 1rem; }
}
```

**Use cases:** Managing specificity, organizing vendor code


## :has() Selector

**Browser Support:** Chrome 105+, Safari 15.4+, Firefox 121+ (2023+)

Parent selector based on children:

```css
/* Card with image gets different layout */
.card:has(img) {
  display: grid;
  grid-template-columns: 200px 1fr;
}

/* Form validation styling */
.form-group:has(input:invalid) {
  border-color: red;
}
```

**Use cases:** Parent styling, state-based layouts


## Logical Properties

**Browser Support:** Chrome 89+, Safari 15+, Firefox 66+ (2021+)

Direction-agnostic spacing:

```css
/* Instead of margin-left */
.element {
  margin-inline-start: 1rem;
  padding-block: 2rem;
  border-inline: 1px solid #ccc;
}
```

**Use cases:** Internationalization, RTL support


## Modern Color Functions

**Browser Support:** Varies by function

### color-mix()
**Support:** Chrome 111+, Safari 16.2+, Firefox 113+ (2023+)

```css
.element {
  background: color-mix(in srgb, blue 50%, white);
}
```

### oklch()
**Support:** Chrome 111+, Safari 15.4+, Firefox 113+ (2023+)

```css
.element {
  color: oklch(0.5 0.2 180);  /* Perceptually uniform */
}
```


## Subgrid

**Browser Support:** Chrome 117+, Safari 16+, Firefox 71+ (2023+)

Inherit parent grid tracks:

```css
.grid-container {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
}

.nested-grid {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
}
```


## aspect-ratio Property

**Browser Support:** Chrome 88+, Safari 15+, Firefox 89+ (2021+)

```css
.video-container {
  aspect-ratio: 16 / 9;
  width: 100%;
}
```


## gap Property (Flexbox)

**Browser Support:** Chrome 84+, Safari 14.1+, Firefox 63+ (2020+)

```css
.flex-container {
  display: flex;
  gap: 1rem;  /* No more margin hacks! */
}
```


## clamp(), min(), max()

**Browser Support:** Chrome 79+, Safari 13.1+, Firefox 75+ (2020+)

```css
.text {
  font-size: clamp(1rem, 2.5vw, 2rem);
  width: min(90%, 1200px);
  padding: max(1rem, 3vw);
}
```


## Custom Properties Improvements

### @property (Typed Custom Properties)
**Support:** Chrome 85+, Safari 16.4+, Firefox (limited) (2023+)

```css
@property --my-color {
  syntax: '<color>';
  inherits: false;
  initial-value: blue;
}

.element {
  --my-color: red;
  transition: --my-color 0.3s;  /* Can now animate! */
}
```


## View Transitions API

**Browser Support:** Chrome 111+, Safari (limited), Firefox (in progress) (2023+)

```css
@view-transition {
  navigation: auto;
}

::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 0.3s;
}
```


## :is() and :where() Selectors

**Browser Support:** Chrome 88+, Safari 14+, Firefox 78+ (2020+)

```css
/* :is() - maintains specificity */
:is(h1, h2, h3):hover {
  color: blue;
}

/* :where() - zero specificity */
:where(.card, .panel) {
  padding: 1rem;
}
```


## accent-color Property

**Browser Support:** Chrome 93+, Safari 15.4+, Firefox 92+ (2022+)

```css
input[type="checkbox"] {
  accent-color: #0066cc;
}
```


## Animation Improvements

### animation-timeline (Scroll-driven animations)
**Support:** Chrome 115+, Safari (in progress), Firefox (in progress) (2023+)

```css
.fade-in {
  animation: fade linear;
  animation-timeline: view();
}
```

### animation-composition
**Support:** Chrome 112+, Safari 16+, Firefox 115+ (2023+)

```css
.element {
  animation: move 1s, scale 1s;
  animation-composition: add;  /* Combine instead of override */
}
```


## Performance Considerations

- **Container queries:** Slight performance cost, use judiciously
- **:has():** More expensive than child selectors, avoid in hot paths
- **Custom properties:** Can now animate with @property
- **Nesting:** No performance difference from Sass output
- **Logical properties:** Same performance as physical properties


## Progressive Enhancement Strategy

1. Use feature queries for cutting-edge features:
```css
@supports (container-type: inline-size) {
  .card-container {
    container-type: inline-size;
  }
}
```

2. Provide fallbacks for critical layouts
3. Consider build tools for wider support (autoprefixer, etc.)
4. Test in target browsers


## Replacing Sass Features

**Some modern CSS can replace Sass:**
- Native nesting ≈ Sass nesting (different syntax)
- CSS variables ≈ Sass variables (with different capabilities)
- calc() ≈ Some Sass math

**Sass still valuable for:**
- Build-time logic and conditionals
- Color manipulation functions (until more color functions land)
- Mixins with complex logic
- Modular imports with namespaces
- Your existing workflow


## Resources

- [Can I Use](https://caniuse.com) - Browser support tables
- [MDN Web Docs](https://developer.mozilla.org) - Detailed documentation
- [CSS Tricks](https://css-tricks.com) - Practical examples
- [Baseline](https://web.dev/baseline) - Newly available features