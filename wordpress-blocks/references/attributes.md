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
