# Media Upload Pattern

Single-image picker for custom Gutenberg blocks using WordPress core's `MediaUpload` / `MediaUploadCheck` components. Store both `imageId` (canonical) and `imageUrl` (render-time fallback if the attachment is deleted). For blocks with multiple image fields (cards, items, slides), see [multiple-items.md](multiple-items.md) for the helper-function wrapping pattern.

## Image Upload Attributes

**PHP:**
```php
'imageId' => array(
    'type' => 'number',
    'default' => 0
),
'imageUrl' => array(
    'type' => 'string',
    'default' => ''
),
```

## Image Upload in JavaScript

```javascript
const { MediaUpload, MediaUploadCheck } = wp.blockEditor;
const { Button } = wp.components;

// In edit function:
el(MediaUploadCheck, {},
    el(MediaUpload, {
        onSelect: function(media) {
            setAttributes({
                imageId: media.id,
                imageUrl: media.url
            });
        },
        allowedTypes: ['image'],
        value: attributes.imageId,
        render: function(obj) {
            return el('div', { className: 'media-upload-wrapper' },
                attributes.imageUrl ? 
                    el('div', {},
                        el('img', {
                            src: attributes.imageUrl,
                            style: { maxWidth: '200px', display: 'block', marginBottom: '10px' }
                        }),
                        el(Button, {
                            onClick: obj.open,
                            className: 'button'
                        }, 'Change Image'),
                        el(Button, {
                            onClick: function() {
                                setAttributes({
                                    imageId: 0,
                                    imageUrl: ''
                                });
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
)
```

## Image Rendering in PHP

```php
// Get image URL from ID
$image_url = '';
if (isset($attributes['imageId']) && $attributes['imageId']) {
    $image_url = wp_get_attachment_image_url(absint($attributes['imageId']), 'full');
} elseif (isset($attributes['imageUrl'])) {
    $image_url = esc_url($attributes['imageUrl']);
}

// Render in template
<?php if ($image_url) : ?>
    <img src="<?php echo esc_url($image_url); ?>" alt="" class="block-image">
<?php endif; ?>
```
