# Multiple Item Blocks

Pattern for blocks with a **fixed count** of repeating items (3 cards, 4 callout boxes). Each item gets its own flat-namespaced attributes (`item1Header`, `item2Header`, …). For arbitrary user-added lists, use core `InnerBlocks` instead — that's not covered here. For escaping every attribute on render, see [security.md](security.md).

## When to use this pattern

- Fixed count, decided at block-design time (e.g., a "Three Resources" block)
- Each item has the same shape (image + header + subhead + link)
- Editors should NOT be able to add or remove items — that's a content-shape decision

For variable counts, use core `InnerBlocks` or convert to a parent + repeated child blocks.

## PHP Attributes for Multiple Items

```php
'attributes' => array(
    'blockTitle' => array(
        'type' => 'string',
        'default' => 'Additional Resources'
    ),
    // Item 1
    'item1ImageId' => array('type' => 'number', 'default' => 0),
    'item1ImageUrl' => array('type' => 'string', 'default' => ''),
    'item1Header' => array('type' => 'string', 'default' => 'Item 1 Title'),
    'item1Subhead' => array('type' => 'string', 'default' => 'Item 1 description'),
    'item1Link' => array('type' => 'string', 'default' => '/item-1/'),
    // Item 2
    'item2ImageId' => array('type' => 'number', 'default' => 0),
    'item2ImageUrl' => array('type' => 'string', 'default' => ''),
    'item2Header' => array('type' => 'string', 'default' => 'Item 2 Title'),
    'item2Subhead' => array('type' => 'string', 'default' => 'Item 2 description'),
    'item2Link' => array('type' => 'string', 'default' => '/item-2/'),
    // Item 3
    'item3ImageId' => array('type' => 'number', 'default' => 0),
    'item3ImageUrl' => array('type' => 'string', 'default' => ''),
    'item3Header' => array('type' => 'string', 'default' => 'Item 3 Title'),
    'item3Subhead' => array('type' => 'string', 'default' => 'Item 3 description'),
    'item3Link' => array('type' => 'string', 'default' => '/item-3/'),
),
```

## Helper Function for Media Uploaders

```javascript
function renderMediaUpload(itemNum) {
    const imageIdAttr = 'item' + itemNum + 'ImageId';
    const imageUrlAttr = 'item' + itemNum + 'ImageUrl';
    
    return el(MediaUploadCheck, {},
        el(MediaUpload, {
            onSelect: function(media) {
                const attrs = {};
                attrs[imageIdAttr] = media.id;
                attrs[imageUrlAttr] = media.url;
                setAttributes(attrs);
            },
            allowedTypes: ['image'],
            value: attributes[imageIdAttr],
            render: function(obj) {
                return el('div', { className: 'media-upload-wrapper' },
                    attributes[imageUrlAttr] ? 
                        el('div', {},
                            el('img', {
                                src: attributes[imageUrlAttr],
                                style: { maxWidth: '200px', display: 'block', marginBottom: '10px' }
                            }),
                            el(Button, {
                                onClick: obj.open,
                                className: 'button'
                            }, 'Change Image'),
                            el(Button, {
                                onClick: function() {
                                    const attrs = {};
                                    attrs[imageIdAttr] = 0;
                                    attrs[imageUrlAttr] = '';
                                    setAttributes(attrs);
                                },
                                className: 'button',
                                style: { marginLeft: '10px' }
                            }, 'Remove')
                        ) :
                        el(Button, {
                            onClick: obj.open,
                            className: 'button button-primary'
                        }, 'Upload Image')
                );
            }
        })
    );
}

// Use in edit function:
el('h4', {}, 'Item 1'),
renderMediaUpload(1),
el(TextControl, {
    label: 'Header',
    value: attributes.item1Header,
    onChange: function(value) {
        setAttributes({ item1Header: value });
    }
}),
// ... more fields
```
