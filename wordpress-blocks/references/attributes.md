# Block Attribute Types

Reference for the most common attribute types in custom Gutenberg blocks. Pair each PHP attribute declaration with its matching JavaScript editor control. Defaults set in PHP `register_block_type()` MUST match defaults in the JS `attributes` object — mismatches cause silent breakage in the editor.

## Text Fields

**PHP:**
```php
'textField' => array(
    'type' => 'string',
    'default' => 'Default text'
),
```

**JavaScript:**
```javascript
el(TextControl, {
    label: 'Text Field',
    value: attributes.textField,
    onChange: function(value) {
        setAttributes({ textField: value });
    }
})
```

## Textarea Fields

**PHP:**
```php
'textareaField' => array(
    'type' => 'string',
    'default' => 'Default longer text'
),
```

**JavaScript:**
```javascript
el(TextareaControl, {
    label: 'Textarea Field',
    value: attributes.textareaField,
    onChange: function(value) {
        setAttributes({ textareaField: value });
    },
    rows: 6
})
```

## Number Fields

**PHP:**
```php
'numberField' => array(
    'type' => 'number',
    'default' => 0
),
```

**JavaScript:**
```javascript
el(TextControl, {
    label: 'Number Field',
    type: 'number',
    value: attributes.numberField,
    onChange: function(value) {
        setAttributes({ numberField: parseInt(value) });
    }
})
```

## Boolean Fields

For show/hide toggles, feature flags, or any binary state. Pair `'type' => 'boolean'` with `ToggleControl` in the editor.

**PHP:**
```php
'showHeader' => array(
    'type' => 'boolean',
    'default' => true
),
```

**JavaScript:**
```javascript
const { ToggleControl } = wp.components;

el(ToggleControl, {
    label: 'Show Header',
    checked: attributes.showHeader,
    onChange: function(value) {
        setAttributes({ showHeader: value });
    }
})
```

**PHP render:** cast explicitly before use — Gutenberg can serialize boolean attributes as `1`/`0` or `true`/`false` depending on path. `filter_var()` handles both reliably.

```php
$show_header = filter_var(
    $attributes['showHeader'] ?? false,
    FILTER_VALIDATE_BOOLEAN
);

if ($show_header) {
    echo '<h2>' . esc_html($title) . '</h2>';
}
```

## Pitfall: PHP and JS defaults must match

The `'default'` value in `register_block_type()` (PHP) MUST match the `default` in `registerBlockType()` (JavaScript). When they differ, Gutenberg silently uses one of them depending on which side initializes the attribute first — and you'll waste hours debugging missing fields, wrong values, or attributes that "reset on save."

**Wrong:**
```php
// PHP
'blockTitle' => array('type' => 'string', 'default' => 'Default Title'),
```
```javascript
// JS — same key, different default
blockTitle: { type: 'string', default: '' },
```

**Right:** keep the strings byte-for-byte identical, or set the default in one place and omit it in the other (PHP defaults flow through to the editor when the JS side omits `default`).

For escaping every attribute on render, see [security.md](security.md).
