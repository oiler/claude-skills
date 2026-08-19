# Punctuation

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: colons, commas, dashes, ellipses, hyphens, parentheses, periods, quotation-marks, semicolons, slashes

## Colons

A colon signals that closely related information follows. When a colon introduces a list, everything before the colon has to stand alone as a complete sentence, which rules out the common shortcut of ending the lead-in with `are:`. The first word after a colon is lowercase, except for a proper noun, a heading, a quotation, or text after a label such as `Caution`.

The `colons` rule reports three shapes as warnings: a heading that ends in a colon, a space before a colon, and a double colon. Only the first has a guide page behind it, and that page is `headings` rather than `colons`; the other two are workshop punctuation hygiene.

| Recommended | Not recommended |
|---|---|
| `The fields are defined as follows:` | `The fields are:` |
| `Tone: concise, conversational, friendly, respectful` | `Tone: Concise, conversational, friendly, respectful` |
| `Install the dependencies` | `Install the dependencies:` |

## Commas

The serial comma is required. A series of three or more items takes a comma before the final `and` or `or`, because leaving it out can change what the sentence means. Beyond the series, commas do three more jobs. One follows an introductory word or phrase. One separates two independent clauses joined by a coordinating conjunction, unless both clauses are very short. One precedes a `which` that opens a nonrestrictive clause. A conjunctive adverb such as `however` or `otherwise` takes a semicolon, period, or dash before it and a comma after it. Don't put a comma before a causal `because` unless it opens a nonrestrictive clause.

The `oxford-comma` rule reports a missing serial comma as an error. It has two known blind spots, both deliberate. It skips a clause that opens with a subordinator or ends with a conjunctive adverb, and it skips a sequence where the segment after the comma opens with a connective, so neither `If you are done, click Save and close the tab` nor `Save the file, then commit and push` is reported. Both suppressors trade a few missed findings for a rule that doesn't fire on correctly punctuated prose.

| Recommended | Not recommended |
|---|---|
| `Locations are divided into zones, regions, and multi-regions.` | `Locations are divided into zones, regions and multi-regions.` |
| `Finally, only groups that contain parameters appear in this list.` | `Finally only groups that contain parameters appear in this list.` |
| `The libraries make feed creation easier, and they ensure that only valid feeds are produced.` | `The libraries make feed creation easier and they ensure that only valid feeds are produced.` |
| `Type your ID and click OK.` | `Type your ID, and click OK.` |
| `Name of the group, which has a maximum length of 200 characters.` | `Name of the group which has a maximum length of 200 characters.` |
| `The variable must have a value; otherwise, the server returns an error.` | `The variable must have a value otherwise the server returns an error.` |

## Dashes

An em dash marks a break or interruption in a sentence, and the guide closes it up: no space before it, no space after it. Don't substitute an en dash or a hyphen for an em dash, and don't use a spaced dash of any length to separate an item from its description; a colon or a period does that job, and a description list does it for a series. The guide retires the en dash outright. Use a hyphen or the word `to` instead.

Ranges are the corrected fact here, and they cut against the intuition that a range always takes `to`. A range of bare numbers takes a hyphen with no spaces: `2012-2016` and `5-10 minutes` are the guide's own recommended forms. The word `to` becomes mandatory only when the range carries a unit, because a hyphen next to a unit reads as a minus sign. The guide counts a symbol such as `°C` and an abbreviation such as `MB` as units, but not a noun such as `file`. Repeat the unit on both numbers. And don't mix the two conventions: `from 8-20 files` is wrong either way.

The `em-dash` rule reports `--` used as an em dash as an error. It reports a spaced em dash as a warning rather than an error, which is a deliberate deviation from the guide: oiler's house style spaces em dashes, and `CLAUDE.md` outranks this skill. The warning stays so the guide's own rule is still visible; the severity drops so the house style isn't gated against.

| Recommended | Not recommended |
|---|---|
| `To indicate a break in the flow of a sentence—or an interruption—use an em dash.` | `To indicate a break in the flow of a sentence -- or an interruption -- use an em dash.` |
| `Example: This is an example.` | `Example - This is an example.` |
| `Appendix A: My first appendix` | `Appendix A—My first appendix` |
| `-40 °C to 85 °C` | `-40-85 °C` |
| `8-20 files` | `from 8-20 files` |

## Ellipses

In general, don't use ellipses. An ellipsis is three contiguous periods, and when you need one, type three periods in a row rather than the single ellipsis character. Don't use ellipses as suspension points to signal hesitation, and don't carry them over from a user interface label; a button reading `Save ...` is documented as `click Save`.

Ellipses belong in exactly one place: quoted text, standing in for material you cut from the middle. They don't go at the beginning or the end of a quotation. When the omitted material crosses a sentence boundary, use four dots, because the last one is a period. Put one space before and after the ellipsis, unless a punctuation mark follows it directly.

The `ellipsis` rule reports both the single character and the three-period form as warnings, because outside a quotation neither belongs in the prose.

| Recommended | Not recommended |
|---|---|
| `Omit the unnecessary information and include all the necessary information.` | `The answer is ... wait for it ... that you shouldn't do this.` |
| `click Save` | `click Save ...` |
| `You don't need to understand all the other Python code in there ... it is explained in class.` | `You don't need to understand all the other Python code in there…it is explained in class.` |
| `"All the world's a stage, .... And one man in his time plays many parts."` | `"... all the men and women merely players."` |

## Hyphens

A hyphen earns its place when it prevents a misreading or binds words that should be read as one unit. Hyphenation depends on where the term sits, whether the sentence is ambiguous without it, and what convention the documentation set already follows; when unsure, check the documentation you're working in, then the word list, then Merriam-Webster.

Prefixes generally close up, as in `metadata` and `preprocessing`. Add the hyphen after a prefix when the prefix is `self` or `cross`, when the noun takes a capital letter or a number, when closing up would be hard to read, when the base term already has hyphens or spaces, and where consistency within a document demands it. `non` follows the same guidance but hyphenates more often, because it forms words that are hard to parse.

Compound nouns take their closed form by default: `webpage`, `hostname`, `tradeoff`, `workaround`. Hyphenate a compound modifier before a noun when clarity needs it, avoid modifiers longer than two words, and drop the hyphen when the compound follows a verb. Hyphenate a number with a spelled-out unit that modifies a noun, as in `a 64-bit system`, but not with an abbreviated unit, where a nonbreaking space does the work. Never put a space on either side of a hyphen, except after a suspended hyphen.

Two rules watch this page. The `ly-hyphens` rule reports a hyphen after an adverb ending in `-ly` as an error, since `publicly available` needs no hyphen. The `ranges` rule warns only about a hyphenated range whose closing number carries a unit; a bare numeric range is the recommended form and passes clean.

| Recommended | Not recommended |
|---|---|
| `preprocessing` | `pre-processing` |
| `non-Google` | `nonGoogle` |
| `webpage` | `web page` |
| `A well-designed app` | `A well designed app` |
| `cross-data-center replication` | `edition-2023-specific test cases` |
| `a 64-bit system` | `a 64 bit system` |
| `200 GB disk` | `200-GB disk` |
| `Publicly available implementations` | `Publicly-available implementations` |
| `The app is well designed.` | `The app is well-designed.` |
| `Scan for new files at one-, two-, or three-hour intervals.` | `Scan for new files at one, two, or three-hour intervals.` |

## Parentheses

Readers skip parentheses, so nothing important goes inside them. Even for minor material, check whether the parentheses earn their place; commas, dashes, semicolons, or a second sentence often read better. Keep a mid-sentence parenthetical short, and split the sentence rather than nesting a long thought inside one. A full standalone sentence inside parentheses keeps its period inside; a fragment at the end of a larger sentence takes the period outside. Don't use parentheses for optional plurals.

| Recommended | Not recommended |
|---|---|
| `Enter a name for the instance—for example, my-instance-99.` | `Enter a name for the instance (for example, my-instance-99).` |
| `Enter a six-digit hex number (for example, 228B22), and then click OK.` | `Enter a six-digit hex number (for example, if you want the color forest green, enter 228B22), and then click OK.` |
| `App Engine applications are easy to create and to scale. (With App Engine, there are no servers for you to maintain.)` | `App Engine applications are easy to create and to scale (With App Engine, there are no servers for you to maintain).` |

## Periods

End a complete sentence with a period unless it's a question. List items follow the list guidance instead, and headings take no period at all. Leave one space between sentences.

A period after a URL is ambiguous, so rewrite the sentence to move the URL off the end, or put the URL on its own line without the period. A period goes inside closing quotation marks, even when it isn't part of the quoted material, and a period after a parenthetical goes outside the closing parenthesis unless the parentheses hold a whole sentence. Use a period as the decimal point. Keep the period on a shortened word and drop it from an acronym.

Exclamation points are the sharp edge of this page. Concept and reference documentation never uses one. Procedures avoid it. Blog posts may carry it for enthusiasm, and tutorials may use it sparingly to mark a milestone. Code samples and system literals use it where the syntax or the log line demands it, as with the `!=` operator. The `exclamation` rule reports `!` as a warning; the `spacing` rule reports a double space between sentences, and a space before a comma or semicolon, as errors.

| Recommended | Not recommended |
|---|---|
| `In accordance with the Privacy Policy: http://www.examplepetstore.com/privacy/` | `In accordance with the Privacy Policy at http://www.examplepetstore.com/privacy/.` |
| `...you might say "Fixed typo."` | `...you might say "Fixed typo".` |
| `Children always ask "Why?"` | `Children always ask "Why?".` |
| `The VM is created.` | `The VM is created!` |
| `The setup is complete.` | `The setup is complete.  Next, deploy the app.` |

## Quotation marks

Use straight double quotation marks and straight apostrophes, never the curly forms. Tools that convert them make mistakes, humans typing them make mistakes, and proofreading can't tell them apart at a glance. Technical writing needs quotation marks rarely: titles of shorter works, a section you can't link to directly, a direct citation, and a term used metaphorically where the metaphor isn't already established in the domain.

Commas and periods go inside the quotation marks. The exception is a literal string: when quotation marks mark an exact keyword, any other punctuation goes outside them, so nothing extraneous lands inside the literal. In general, don't wrap an item in quotation marks when it's already in code font. Single quotation marks appear only in code examples in languages that use them, and around a quotation nested inside another quotation.

The `quotes` rule reports a period or comma sitting outside a closing double quotation mark as a warning.

| Recommended | Not recommended |
|---|---|
| `See the section titled "Care and feeding of the emu."` | `See the section titled "Care and feeding of the emu".` |
| `The section's title is "Care and feeding of the emu."` | `The section’s title is “Care and feeding of the emu.”` |
| `If you enter escape, the program crashes.` | `If you enter "escape," the program crashes.` |
| `She said, "I heard him shout 'Help,' and saw him floundering in the water."` | `She said, 'I heard him shout "Help", and saw him floundering in the water'.` |

## Semicolons

Avoid semicolons where you can. Three cases justify one: joining two closely related independent clauses where neither a period nor a comma works as well, standing before a conjunctive adverb such as `therefore` or a phrase such as `that is` that joins two independent clauses, and separating a series of long or complex items that carry their own internal punctuation.

The `semicolons` rule applies narrowly rather than globally. It warns about a semicolon only inside a procedural step, where a reader following instructions has to hold two actions in one line, and it leaves semicolons in running prose alone.

| Recommended | Not recommended |
|---|---|
| `This setup places the head-tracked node below the Main Camera; therefore, only the stereo cameras are affected by the user's head motion.` | `This setup places the head-tracked node below the Main Camera, therefore only the stereo cameras are affected by the user's head motion.` |
| `Review your document one more time, checking for the following: present tense and active voice; typos, punctuation, and grammar; and whether you can shorten anything.` | `Review your document one more time, checking for the following: present tense and active voice, typos, punctuation, and grammar, and whether you can shorten anything.` |
| `Open the file. Set the timeout to 30 seconds.` | `Open the file; set the timeout to 30 seconds.` |

## Slashes

Avoid slashes outside code. Don't use them to separate alternatives; `and` or `or` says what you mean. Don't use them in dates; don't use them in fractions, which are ambiguous, because `3/4` can read as three-quarters or as `4` offered as an alternative to `3`; and don't use them in abbreviations such as `c/o` or `w/`, which spell out as `care of` and `with`. The `and/or` construction is its own entry on the word list, and the `word-list` rule reports it as an error; write `or`, or name both cases.

Slashes keep their meaning in file paths and URLs. Use forward slashes there, backslashes in a Windows path, and break a long URL immediately after a slash rather than inserting a hyphen.

| Recommended | Not recommended |
|---|---|
| `Call this method five or six times.` | `Call this method 5/6 times.` |
| `The map is not subject to the usage limits even if it has been developed or is hosted by a commercial entity.` | `The map is not subject to the usage limits even if it has been developed/hosted by a commercial entity.` |
| `You can export raw events, processed events, or both.` | `You can export raw and/or processed events.` |
| `0.75` | `3/4` |
| `care of, with` | `c/o, w/` |
