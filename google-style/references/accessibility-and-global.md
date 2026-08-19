# Accessibility and global audiences

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: accessibility, translation, inclusive-documentation

## Write accessibly

Directional language is the rule this page is built around, and it fails twice over. `above`, `below`, and `see the box on the right` assume the reader sees a laid-out page, which a screen reader user doesn't, and they assume a left-to-right layout, which a right-to-left language doesn't have. Text isn't below anything when a screen reader is reading it aloud. Describe the target instead: name the button by its label, use `earlier`, `preceding`, or `following` for a position in the document, add context such as the toolbar an icon sits on, or supply a screenshot. Never describe a visual element by its shape, so `Click Menu` rather than `Click the button with three lines`.

Nothing conveys information by color, size, position, or any other visual cue alone. Where color or an outline signals state, a text label carries the same signal. Contrast ratios meet 4.5:1 for text. `visibility:hidden` and `display:none` hide content from screen readers, so neither is a way to store information. A mouseover event needs matching focus and blur events for keyboard users, and every part of the page, including tabs, buttons, and interactive elements, has to be reachable with the keyboard alone. The check the guide gives is to read your own document without sound, with sound alone, without images, without color, without punctuation, with a keyboard, and under magnification, and confirm that every intended meaning still arrives.

Structure and formatting do most of the work. Tag headings as headings, keep the hierarchy, skip no level, leave none empty, and give the page title a level-1 heading. Sentences run under 26 words. Paragraphs, headings, and lists break up walls of text, and the distinguishing information leads the paragraph. Define an acronym on first use. Avoid camel case and all-capitals where you can, because some screen readers read capitals letter by letter and some languages have no case at all. Punctuation isn't always read aloud, so the meaning has to survive without the exclamation marks, question marks, and semicolons; write so it does. Don't force hard line breaks, and don't use an ampersand where the word `and` belongs.

Elements have their own requirements. Every image carries an `alt` attribute; the value is informative text, or the empty string. Introduce a table in the text before it. Use `th` for the first row and the first column, carry `scope` where both exist, and never merge cells. An interactive element gets an introduction in the text before it. A form input has a `label` element outside the field, and a validation error says what went wrong and how to fix it. An angle-bracket menu path carries an `aria-label` so the bracket reads as `and then`. Video and audio come with captions, transcripts, or descriptions, translatable into major languages, and nothing on the page flickers or flashes.

| Recommended | Not recommended |
|---|---|
| `In the preceding diagram, clients run jobs on multi-team clusters.` | `In the diagram above, clients run jobs on multi-team clusters.` |
| `Click Menu.` | `In the left-side panel, click the button with three lines.` |
| `Click Notifications.` | `Click the bell icon.` |
| `You can continue without a path.` | `A missing path won't prevent you from continuing.` |
| `<img src="diagram.svg" alt="Bounded contexts applied to an application.">` | `<img src="diagram.svg">` |
| `Search and filter` | `Search & filter` |

## Write for a global audience

Documentation gets read by people whose first language isn't English, and translated into languages that aren't English, so write for both from the start. Shorter sentences translate better and cost less to translate, because an English sentence of ordinary length can become a long one in another language. Simple words beat elaborate ones: `start` rather than `commence`, `so` rather than `consequently`, `use` in place of `utilize` or `leverage`, `some` or `many` in place of `a number of`. Phrasal verbs get replaced by single verbs where a single verb exists, though `set up`, `log in`, and `sign in` have no better form. Stack no more than two nouns in front of another noun, and put a word such as `only` immediately before what it modifies.

Consistent terminology isn't a stylistic preference, and it's the reason repetition beats variation here. One concept keeps one term, with the same capitalization, everywhere it appears. A synonym the reader has to resolve costs more than the repetition saves, and it costs more still in translation: a translator seeing two names assumes two concepts and produces two translations, and translation memory and machine translation compound the divergence. The same consistency applies to sentence structure, formatting, and capitalization. Use standardized phrases for recurring jobs such as introducing a link, an output block, or a code sample.

Helper words that conversational English drops belong back in the sentence. Keep `then`, `that`, and `of`. Keep the relative pronouns `that` and `which`. Repeat a word where the redundancy removes an ambiguity. Three habits help a reader parsing English as a second language as much as they help a translator. Use standard subject-verb-object order. Keep the main subject and verb near the front of the sentence. Put the conditional clause before the instruction. Present tense and active voice do the same, because a passive sentence hides who acts. Define abbreviations, and replace any pronoun with a slightly unclear antecedent with the noun itself.

Culture travels worse than grammar. Idioms don't translate: `under the hood` earns its word list entry for exactly this reason, and `ballpark figure`, `back burner`, and `hang in there` are the same problem. Humor is usually both untranslatable and culturally specific. Holidays, sports, and cultural practices don't generalize, seasons invert between hemispheres, and dates need an unambiguous format. Use a diverse set of example names. Images don't get translated at all, so keep new information out of them.

| Recommended | Not recommended |
|---|---|
| `This document uses the following terms:` | `This document makes use of the following terms:` |
| `Request only one token.` | `Only request one token.` |
| `A cloud-native DevSecOps pipeline in a hybrid environment` | `A hybrid cloud-native DevSecOps pipeline` |
| `If the attribute key isn't found, then the service returns the default value.` | `If the attribute key is not found, the default value is returned.` |
| `Start the profiler, and then run the app.` | `Start the profiler, then run the app.` |
| `You can programmatically update the rules that you previously defined.` | `You can programmatically update the rules you previously defined.` |
| `internally, or describe the mechanism` | `under the hood` |

## Inclusive language

Gendered language has two sources, and both are avoidable. Pronouns come first: don't use `he`, `him`, `his`, `she`, or `her` as a gender-neutral pronoun, and don't reach for `he/she` or `(s)he` either. The singular `they` is the form. Role nouns come second, and `man-hours`, `mankind`, and `manpower` all have plain replacements in `person-hours`, `humanity`, and `staffing`. The `gendered` rule reports both groups as errors.

Ableist language is words that use disability as a metaphor for something bad. `crazy`, `insane`, `lame`, `cripples`, `dumb`, `sanity-check`, `blind to`, and `deaf to` are the ones the `ableist` rule reports, all as errors, and each has a more accurate replacement: outliers are baffling, a queue is slowing the service, a check is one for completeness, and a reader is unaware of something. Writing about disability itself asks for more care than a word list can carry. Don't call people without disabilities `normal` or `healthy`. Research how a community identifies itself, since person-first phrasing suits some communities and identity-first phrasing suits others, including autistic, blind, and Deaf communities. Skip terms that project feeling onto a person's disability, `victim of` and `wheelchair-bound` among them, and skip the euphemisms such as `differently abled`.

Figurative language is the broader category all of this sits inside. A metaphor is imprecise, translates badly, and often carries something you didn't intend, so use words in their primary sense. That rules out `pets versus cattle` for stateless systems, `STONITH` where `fence a failed node` says it, `hangs` where `doesn't respond` says it, and `hit` where `press` or `click` says it. Socially charged terms for technical concepts go too: `blacklist` becomes `allowlist` and `denylist`, `dummy` becomes `placeholder`, and `first-class citizen` becomes a description of what the thing actually supports.

Two escape hatches exist for terms you can't remove. Where an established industry term would confuse readers if it vanished, name it once in parentheses on first use, then use the inclusive term throughout: `an allowlist (sometimes called a whitelist)`. Where the term is a name or a keyword inside code, keep it in code font, name it once in parentheses if you can, and use the preferred term everywhere else, so a `master` cluster in a config file becomes the parent node in the prose around it. Often the better move is neither: rewriting the sentence removes the term entirely, which is why `allow requests from a range of IP addresses` beats any noun choice at all.

| Recommended | Not recommended |
|---|---|
| `Equipment installation takes around 16 person-hours.` | `Equipment installation takes around 16 man-hours.` |
| `Build AI that benefits humanity.` | `Build AI that benefits mankind.` |
| `Give everything a final check for completeness and clarity.` | `Give everything a final sanity-check.` |
| `There are some baffling outliers in the data.` | `There are some crazy outliers in the data.` |
| `It slows down the service until the queue clears.` | `It cripples the service until the queue clears.` |
| `Replace the placeholder with the appropriate value.` | `Replace the dummy variable with the appropriate value.` |
| `Point to File, and then click New.` | `Hover over File, and hit New.` |
| `If the connection doesn't respond, check for errors.` | `If the connection hangs, check for errors.` |
| `an allowlist (sometimes called a whitelist)` | `a whitelist` |
| `a parent node (which is named master in the file)` | `the master node` |
