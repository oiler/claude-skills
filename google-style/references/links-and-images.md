# Links and images

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: cross-references, headings-targets, images

## Cross-references and linking

Every link is a decision the reader has to make and a chance for them to leave the page. Link selectively, and always to the single most relevant destination. Where the reader needs a definition, a short explanation of a concept, or a couple of steps, put that on the page instead of linking away. Linking earns its place where the reader needs another product's standards or software, which is worth a link rather than a partial restatement. Within a page, don't repeat a link to the same destination, unless the page is long enough that the copies sit far apart, the target is a specific section, or the page has entry points that a reader can arrive at separately.

Link text is where accessibility lives, because screen reader users often jump from link to link without the words between them, and sighted readers scan for links the same way. Link text is therefore short, unique within the document, and descriptive enough to stand alone, with the important words at the front. Two forms work: the exact page title or heading, or a descriptive phrase capitalized as part of the sentence. A URL isn't link text, outside some legal documents. The `link-text` rule reports the vague forms as errors, and its list is the guide's list: `click here`, a bare `here`, `this`, `this link`, `this page`, `read more`, `more`, `link`, `learn more`, `see here`, and `documentation`. Rework the sentence where it doesn't contain a phrase worth linking.

Two inclusions extend the link text rather than sitting beside it. Where a term has an abbreviation in parentheses, the long form goes inside the link along with the abbreviation. Where the link is a command or another code element, the description of that element joins the link text, so `the gcloud instances create command` is the link rather than the bare command name.

A cross-reference in its own sentence uses fixed wording: `For more information, see …`, extended to `For more information about …, see …` where the link text alone doesn't say why the reader should follow it. Two separate rules govern the wording. Don't use `on` where `about` belongs. Use `see` to refer to a link or a cross-reference. Beyond those, don't repeat the link text in the explanation. Explain any link that behaves unexpectedly: a link that downloads a file names the file type, a link that opens email says so, a link to another section on the same page says it goes to a section of this document, and a link that opens in a new tab says so in the link text. Better still, don't force a new tab at all, and don't mark an external destination with an icon; say it in the text.

Punctuation before or after a link sits outside the link tags. A cross-reference that's a link takes no quotation marks. A cross-reference that isn't a link takes quotation marks for a section or a short work, and italics for a full-length work. Avoid external links in the navigation of a documentation set. Where sitewide CSS is yours to write, style link text so it contrasts with body text, underline link text but nothing else, and change the color of a visited link using a color-blind-friendly pair.

| Recommended | Not recommended |
|---|---|
| `For more information, see Make headings into link targets.` | `Want more? Click here.` |
| `For more information about task scheduling, see Reliable task scheduling.` | `For more information on indexes, see Manage indexes.` |
| `[Google Kubernetes Engine (GKE)](...)` | `[Google Kubernetes Engine](...) (GKE)` |
| `run the [gcloud instances create command](...)` | `run the [gcloud instances create](...) command` |
| `For more information, see [HTTP/1.1 RFC](http://www.w3.org/Protocols/rfc2616/rfc2616.html).` | `See the HTTP/1.1 RFC at [http://www.w3.org/...](http://www.w3.org/...).` |
| `[Accessible content (opens in a new tab)](/style/accessibility)` | `<a href="/style/accessibility" target="_blank">Accessible content</a>` |
| `For more information, see [Test your code](#Test).` | `For more information, see [Test your code.](#Test)` |

## Headings as link targets

A content management system usually generates an anchor from the heading text, which means the anchor breaks the moment somebody rewords the heading. A custom anchor decouples the two. Three cases justify adding one: the generated anchor is longer than it needs to be, the section is one that other pages link to often, or you're about to revise the heading and want existing links to survive.

Anchor text is lowercase with hyphens between words, the same convention filenames follow. HTML has several forms: a `section` element carrying an `id`, an `a` element carrying a `name`, or, acceptably, the `id` directly on the heading tag. Markdown appends `{: #ID_OF_ANCHOR }` to the end of the heading line. When you revise a heading that already had a generated anchor, build the custom anchor from the old ID string, which you can read off the published page by inspecting the heading. A heading that already has a custom anchor keeps it, and the one reason to change it is a term that should come out, such as a disrespectful one.

| Recommended | Not recommended |
|---|---|
| `<section id="introduction-to-everything"><h2>Introduction to everything</h2></section>` | `<section id="Introduction_To_Everything">` |
| `## Help conserve habitat for pollinators {: #conserve-habitat }` | `## Help conserve habitat for pollinators {: #ConserveHabitat }` |
| `Keep the old ID as the custom anchor when you reword the heading.` | `Reword the heading and let the generated anchor change.` |

## Figures and other images

An image earns its place only where it explains something words handle badly. Text, code samples, and terminal output are never images: use the real text, which stays searchable, selectable, and readable by a screen reader. Save a diagram as `SVG` where possible, because a vector stays sharp at any zoom, and as `PNG` where no vector exists. Skip transparent backgrounds. Animations use a resource-efficient format such as `MP4` rather than an animated `GIF`. Screenshots stay consistent across a document in the operating system they come from and in how they look, and they're cropped to the part that matters, which also helps them survive an interface change. Never put personally identifying information in a screenshot; where the source contains PII, cover it with a solid overlay at full opacity, because anyone can reverse a blur or a mosaic. Image maps are out: they're bad for accessibility, they behave inconsistently across browsers, and the coordinate overlay costs more to maintain than it returns.

Four kinds of text attach to an image, and they do different jobs. An introductory sentence precedes almost every image, ending with a colon where the image follows immediately and a period where something intervenes; a screenshot that directly follows the procedural text describing it needs no introduction. Alt text is a concise replacement for the image, written for its context rather than only its content, in a full sentence or a noun phrase, under 155 characters, with punctuation so the screen reader pauses. It never starts with `Image of` or `Photo of`, avoids all-capitals because some screen readers spell those out letter by letter, and stays consistent across repeated instances of the same image. A figure caption is an optional summary in complete sentences with end punctuation, numbered as `Figure 1.` in a document that numbers its figures. A figure description carries the detail the caption can't, and any new information in a figure belongs there in text.

The `alt` attribute is required on every `img` element, and that includes the decorative case, where the correct value is the empty string. Leaving the attribute out entirely lets a screen reader fall back to reading the filename. A screenshot showing how to fill in fields, an interface icon, and an image that's there to make the page look better are all decorative in this sense: the information already exists in the text, so the empty value keeps assistive technology from repeating it. The test the HTML specification supplies is direct: replacing every image with its alt text shouldn't change the meaning of the page.

Refer to a figure by its number, in lowercase except at the start of a sentence, and never with a spatial description such as `the image above`. Don't repeat the caption inside the sentence that references the figure. Avoid embedding explanatory text inside a graphic, which hurts accessibility and searchability and costs more to localize; where text has to be in the image, keep it brief, use sentence case, avoid inventing abbreviations, and repeat the same information in a figure description.

Serve high-resolution displays with the `img` element's `srcset` attribute alongside `src`. The `src` attribute always stays, pointing at the standard-resolution asset, so an older browser on a low-resolution device downloads the smaller file. The `srcset` attribute lists assets with their multipliers, `1x` and `2x`, and the double-resolution file is exactly twice the width and height of the standard one. Set `width` to the CSS pixel size and let height follow from the proportions. Don't scale a standard image up to fake a double-resolution version; scale down from a high-resolution original, or ship the standard one alone.

| Recommended | Not recommended |
|---|---|
| `The following diagram shows how bounded contexts apply to an ecommerce application:` | `See the diagram.` |
| `alt="Architecture of an app that's built with Apps Script."` | `alt="Image of an architecture diagram"` |
| `<img src="icon.png" alt="">` | `<img src="icon.png">` |
| `Figure 1. Application capabilities are separated into bounded contexts.` | `Bounded contexts` |
| `as shown in figure 1` | `as shown in the image above` |
| `<img src="skateboard.png" srcset="skateboard.png 1x, skateboard_2x.png 2x" width="375" alt="">` | `<img src="skateboard_2x.png" width="375">` |
| `A diagram saved as an SVG file` | `A diagram saved as an animated GIF` |
