# Formatting and structure

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: headings, lists, procedures, paragraph-structure, tables, notices, numbers, dates-times, units-of-measure, format-examples, footnotes, italics-terms, mathematical-notation

## Headings and titles

Every heading and title takes sentence case, and no end punctuation. A task-based heading opens with a bare infinitive, which is the plain form of the verb; a conceptual heading is a noun phrase that doesn't open with an `-ing` verb. Both styles can appear in one document, matched to the section they name. A section that applies only to some readers takes the prefix `Optional:` at the front of the heading, not a parenthetical at the end.

Structure carries the hierarchy. Each page gets one level-1 heading, used once. Levels don't skip, so an `h3` sits only under an `h2`. A heading is always followed by content, never by another heading with nothing between them. Numbers don't go in headings to mark a sequence, links don't go in headings at all, and a code item in a heading needs a descriptive noun next to it. When a group of subsections follows, introduce them as `the following sections`, because `this section` and `these sections` are ambiguous.

The `headings` rule reports two shapes as errors: a heading that ends in a period, and a heading that looks like Title Case, which it detects as two or more capitalized words after the first that aren't proper nouns. The `colons` rule adds a warning for a heading that ends in a colon.

| Recommended | Not recommended |
|---|---|
| `Create an instance` | `Creating an instance` |
| `Migration to Google Cloud` | `Migrating to Google Cloud` |
| `Optional: Customize your alias` | `Customize your alias (optional)` |
| `## Estimate costs` | `### Estimate costs` |
| `Transfer data sets` | `Transfer Data Sets` |
| `The following sections describe the views.` | `These sections describe the views.` |

## Lists

Three list types cover almost everything. A numbered list is for a set whose sequence matters: ordered steps, phases, priorities. A bulleted list is for a set that isn't a sequence, and the introduction has to make clear whether every item is required. A description list is for terms paired with definitions, presented either as term-and-description pairs or as bulleted run-in headings. A single item isn't a list; set it off some other way.

Introduce a list with a complete sentence rather than a fragment that the items finish. The introduction ends with a colon when the list follows immediately, and with a period when something else sits between them. All items share one syntax. Nested sequential lists take lowercase letters, and their nested lists take lowercase Roman numerals.

Capitalization and end punctuation follow the item, not the list. Start each item with a capital letter unless case carries meaning. End each item with a period, except when the item is a single word, when it has no verb, when it's entirely in code font, or when it's entirely link text or a document title. A run-in heading ends with a period or a colon, consistently within the list: text after a period starts capitalized and ends with a period, and text after a colon starts lowercase and takes a period only when it contains a verb or stands as a thought. Don't set a description off with a dash.

A list written inside a paragraph takes serial commas. Don't close one with `etc.` or `and so on`; introduce it so the reader knows it isn't exhaustive. The `latin` rule reports `etc.` as a warning.

| Recommended | Not recommended |
|---|---|
| `Use the Submit button for any of the following purposes:` | `Use the Submit button to:` |
| `To get the USB driver, follow these steps:` | `To get the USB driver:` |
| `Big: a short word` | `Big — a short word` |
| `The service processes data like event logs, clickstream data, and e-commerce transactions.` | `The service processes event logs, clickstream data, e-commerce transactions, etc.` |

## Procedures

A procedure is a sequence of numbered steps, and each step is one action stated with an imperative verb. Small sequential menu selections combine into one step with angle brackets, as in `Click File > New > Document`. Write a procedure of exactly one step as a single bulleted item, with no numbering and no lead-in announcing that a single step follows. Sub-steps take lowercase letters and sub-sub-steps take lowercase Roman numerals, and the parent step ends with a colon or a period the way a list introduction does.

Order inside a step is the whole discipline. The condition or the goal comes before the instruction, so a reader can skip a step that doesn't apply before starting it. The location comes before the action, so `In the Google Cloud console, go to the Monitoring page` rather than the reverse. The action comes before its result or its justification, and both stay in the same paragraph as the action. A complex step runs in this order: the action, the command, the placeholders in the command, any further explanation, the output, and then the result in a separate paragraph. An optional step opens with `Optional:` as its first word.

Directional language has no place in a step. `above`, `below`, and `right-hand side` fail for readers who don't see the page and for translators who can't know the layout. Name the target or show a screenshot instead. Where a task has several possible procedures, document one that works for every reader, preferring the one a keyboard alone can complete, then the shortest. Don't repeat a procedure that already exists elsewhere; link to it. Avoid putting a table in the middle of a numbered procedure.

Two rules watch procedural lines, both warnings, and both fire only when the line opens with an imperative verb. The `condition-order` rule reports an `if`, `when`, or `unless` that arrives after the instruction rather than before it; its source page is `sentence-structure`, not `procedures`. The `semicolons` rule reports a semicolon inside a step, where a reader following instructions would have to hold two actions on one line.

| Recommended | Not recommended |
|---|---|
| `To delete the entire document, click Delete.` | `Click Delete if you want to delete the entire document.` |
| `In Google Docs, click File > New > Document.` | `Click File > New > Document in Google Docs.` |
| `To start a new document, click File > New > Document.` | `Click File > New > Document to start a new document.` |
| `Optional: Type an arbitrary string.` | `(Optional) Type an arbitrary string.` |
| `Click Run. The query results appear after the query runs.` | `Click Run. Then the New file dialog appears, and in it, click Next.` |
| `In the preceding diagram, the load balancer fronts three instances.` | `In the diagram below, the load balancer fronts three instances.` |

## Paragraphs

One paragraph carries one idea, in the fewest sentences and the fewest words that idea needs. The key point goes first, because readers scan rather than read every word. A paragraph running past five or six sentences usually holds more than one idea and wants splitting, though a long paragraph on a single idea is fine, and so is a paragraph of one sentence. Don't lengthen sentences to reduce their count.

Format supports the scan. Text is left-aligned, never centered, right-aligned, or fully justified. Don't force a line break inside a sentence or a paragraph, because a hard return breaks under a resized window, a different screen, or enlarged text.

| Recommended | Not recommended |
|---|---|
| `Left-align text for readability.` | `Center the text for visual balance.` |
| `Break a long paragraph into smaller paragraphs.` | `Lengthen the sentences so the paragraph holds fewer of them.` |

## Tables

The shape of the data picks the presentation. An item that's a single unit belongs in a bulleted, lettered, or numbered list. An item that's a pair belongs in a description list, or sometimes a table. An item carrying three or more related pieces of data belongs in a table. Tables are for two-dimensional data only, so they don't lay out a page, hold code snippets, or split a long one-dimensional list into columns.

Introduce every table with a complete sentence describing its purpose, because not all screen readers announce a table before reading it. Refer to the table's position with `the following table` or `the preceding table`, and don't drop a table into the middle of a sentence. When a document holds more than one table in close proximity, give each a caption in the form `Table 1. Prehistoric birds`, in sentence case with no trailing period, and refer to it by number in lowercase, as in `as shown in table 2`. Prefer referring by number over linking to the table.

Column headings take sentence case, stay concise, and end with no punctuation of any kind. Header cells use the `th` element for the first row and the first column only, with the `scope` attribute set. Don't style the table element. Don't signal a header with color or font alone. Don't merge cells with `colspan` or `rowspan`. Sort rows in a logical order, or alphabetically when no logical order exists. Never carry new information in an image or a symbol alone: the image needs descriptive alt text. Split a long or complicated table into several, and use CSS that adapts to the viewport.

| Recommended | Not recommended |
|---|---|
| `Change the environment variables to values for your deployment, as listed in the following table:` | `See the table.` |
| `Table 1. Prehistoric birds` | `Table 1: Prehistoric Birds.` |
| `as shown in table 2` | `as shown in Table 2` |
| `<th scope="col">Attribute name</th>` | `<td style="font-weight:bold">Attribute name</td>` |

## Notes and other notices

A notice offsets information that sits outside the flow of the text, and readers skip elements outside their focus, so a notice is a weaker place to put something than the prose is. Write the information as ordinary text first, then decide whether it needs offsetting. Several notices on one page cost each of them their distinctiveness, and two notices in a row are a sign that the content wants reorganizing.

Four types cover the range. A `Note` is an aside or a tip: useful, not critical. A `Caution` tells the reader to proceed carefully. A `Warning` is stronger: it means don't do this, or this step can't be undone, and ignoring it costs money, work, or security. A `Success` describes a completed action or an error-free status, and belongs only in interactive or dynamic content, never on a static page.

A note earns its place when all three conditions hold: the information is relevant but not necessary right now, interrupting the reader here isn't an obstacle, and the information isn't a continuation of the surrounding text. That rules out most of what notes get used for. Don't make a note out of a cross-reference, a prerequisite, a step the reader should already have taken, a full procedural step, information the reader needs to succeed, or a restatement of what precedes it.

| Recommended | Not recommended |
|---|---|
| `Note: All VPC networks include firewall rules.` | `Note: See the networking overview for more information.` |
| `Warning: Don't manually edit or delete generated table entries.` | `Note: Don't manually edit generated table entries, or you lose your data.` |
| `Before you begin, enable the API.` | `Note: You must enable the API before you begin.` |

## Numbers

Spell out zero through nine, and use numerals for 10 and greater. Spell out a number that opens a sentence, or rearrange the sentence so the number lands later. Spell out a number that's immediately followed by a numeral, as in `fifteen 100,000-byte files`. Spell out indefinite and casual quantities such as `millions`. Ordinals are always spelled out, which the `ordinals` rule reports as a warning when it finds `1st` or `43rd`.

Numerals win in more places than the ten-and-over rule suggests, and the exceptions apply even below ten: version numbers, technical quantities such as amounts of memory, page, chapter, and step numbers, prices, numbers without units, negative numbers, most fractions, percentages, dimensions, decimals, measurements, numbers in a range, and any number under ten that shares a sentence with a number over nine.

Formatting follows American convention. Commas separate groups of three digits from four digits up, with no separator to the right of the decimal point, and a period serves as the decimal point. A decimal below one carries a leading zero, and a decimal number is plural even at `1.0 inches`. Write fractions as decimals where possible, and hyphenate them when you write them as words. A percentage is a numeral and a `%` with no space, unless it opens the sentence, in which case both the number and the word get spelled out. Dimensions take a lowercase `x` with no spaces, as in `192x192`. A bare numeric range takes a hyphen with no spaces on either side, and never an en dash. Two or more hyphenated compounds modifying the same word take suspended hyphens.

| Recommended | Not recommended |
|---|---|
| `four options` | `4 options` |
| `The link expires in 24 hours.` | `The link expires in twenty-four hours.` |
| `first, fifth, twelfth, forty-third` | `1st, 5th, 12th, 43rd` |
| `The limit is 1,532,784 bytes per day.` | `The limit is 1532784 bytes per day.` |
| `0.3 inches` | `.3 inches` |
| `40%` | `40 %` |
| `192x192` | `192 x 192` |
| `2012-2016` | `2012–2016` |
| `Scan for new files at one-, two-, or three-hour intervals.` | `Scan for new files at one, two, or three-hour intervals.` |

## Dates and times

Times use the 12-hour clock. The exception is content documenting an interface or a command that uses 24-hour time, in which case that format holds for the whole page. Capitalize `AM` and `PM` and leave one space before them, and drop the minutes from a round hour, so `3 PM` rather than `3:00 p.m.`. A time range takes hyphens with no surrounding spaces. Avoid time zones unless the content describes a real event; when a zone is unavoidable, spell the region out, give the offset in parentheses, as in `US and Canadian Pacific Standard Time (UTC-8)`, and never abbreviate the name. The `am-pm` rule reports any other suffix form as an error.

Dates spell the month out in full with a four-digit year: `January 19, 2017`. A day of the week goes before the month. A month-and-year pair takes no comma. A full date in the middle of a sentence takes a comma after the year, though a month-and-year pair mid-sentence doesn't. Abbreviate the month and the day only to save space in a heading or a table cell, using three letters with no period, and abbreviate the whole date or none of it.

Numeric-only dates are the reason this page exists. `04/05/09` means May 4 in the UK, April 5 in the `US`, and May 9, 2004 in parts of the world that lead with the year, so the same nine characters mean three different days. The `date-format` rule reports a numeric date as an error. Where a numeric date is unavoidable, use ISO 8601 `YYYY-MM-DD`, and in a fictional example choose a day past the twelfth so the day can't be read as a month. A date and a time together lead with the date. Avoid seasons entirely, because spring in one hemisphere is autumn in the other; name the month, the quarter, or the temperature.

| Recommended | Not recommended |
|---|---|
| `3 PM` | `3:00 p.m.` |
| `3:45 PM` | `3:45pm` |
| `January 19, 2017` | `12/02/2017` |
| `Tuesday, April 27, 2021` | `Tues, April 27, 2021` |
| `She was hired in January 2017.` | `She was hired in January, 2017.` |
| `2017-04-15 at 3 PM` | `3 PM on 04/15/17` |
| `In November and December, data centers experience higher traffic volume.` | `In winter, data centers experience higher traffic volume.` |

## Units of measurement

A nonbreaking space sits between a number and its unit, in both HTML and Markdown, so `64 GB` rather than `64GB`. The `units` rule reports a number glued to a unit abbreviation as an error. Three cases take no space at all: money, percent, and degrees of an angle. Temperature is the split case: a nonbreaking space sits between the number and the degree symbol, and nothing sits between the degree symbol and the scale letter, giving `50 °C`. Kelvin drops the degree symbol and keeps the space, giving `300 K`.

A range's punctuation turns on whether its numbers carry units. A range of bare numbers takes a hyphen, and that is the guide's recommended form. A range whose numbers carry units takes the word `to`, with the unit repeated on both numbers, because a hyphen beside a unit reads as a minus sign. The guide counts a symbol such as `°` and an abbreviation such as `MB` as units, but not a noun such as `file`. The `ranges` rule fires only on the unit-bearing hyphenated form, as a warning; `5-10 minutes` and `2012-2016` pass clean.

The rest of the page is conventions. Multiplied components of a unit hyphenate, as in `5 vCPU-hours`. A lowercase `k` for thousands takes no space and needs a noun after it, so nobody reads it as kilobytes. Currency needs an indicator wherever the symbol is ambiguous, since `$` covers several currencies. Rates spell out `per` where space allows, and shorten to `p` only in established forms such as `Gbps`. Byte units follow the technology being documented: decimal `kB`, `MB`, and `GB` measure powers of 1000, and binary `KiB`, `MiB`, and `GiB` measure powers of 1024.

| Recommended | Not recommended |
|---|---|
| `64 GB` | `64GB` |
| `50 °C` | `50° C` |
| `300 K` | `300 °K` |
| `$10`, `65%`, `180°` | `$ 10`, `65 %`, `180 °` |
| `-40 °C to 85 °C` | `-40-85 °C` |
| `200 GB disk` | `200-GB disk` |
| `55k download operations` | `55 k downloads` |
| `requests per day` | `requests/day` |
| `US$10` where the currency is ambiguous | `$10` where the currency is ambiguous |

## Examples

Where an example lands in the sentence decides how it's introduced. An example at the end of a sentence is set off with a comma, parentheses, or an em dash, and never a semicolon. An example in the middle of a sentence stays short and takes parentheses, commas, or dashes. A longer example becomes its own sentence, with `for example` used as an adverb inside it rather than as a label in front of it. `such as` and `like` both work as lead-ins.

| Recommended | Not recommended |
|---|---|
| `Choose a strong encryption algorithm, such as AES-256.` | `Enter a name for the instance, for example, my-instance-99.` |
| `You can monitor various metrics—for example, CPU utilization and storage capacity.` | `Specify the region for deployment; for example, us-central1.` |
| `Enter a six-digit hex number (for example, 228B22), and then click OK.` | `Enter a six-digit hex number (for example, if you want the color forest green, enter 228B22), and then click OK.` |
| `You can tag instances by environment. For example, you could use env:prod or env:dev.` | `You can tag instances by environment (for example, you could use env:prod for production instances and env:dev for development instances).` |

## Footnotes

Avoid footnotes. They aren't accessible, and they're a burden to localize. Three alternatives cover nearly every case a footnote would have handled: a cross-reference, a note, or a parenthetical. Where none of them works, a footnote uses a superscript number, and in a table the footnotes sit immediately after the table.

| Recommended | Not recommended |
|---|---|
| `For more information, see the deployment guide.` | `See the deployment guide.1` |
| `Note: This limit applies only to the free tier.` | `This limit applies only to the free tier.2` |

## Italics with terms

Italics do two jobs with terms. Italicize a new term that you define on the spot, on first mention and only on first mention. Italicize a word, phrase, or letter referred to as itself, a usage the guide calls words as words. Neither case takes bold or quotation marks.

| Recommended | Not recommended |
|---|---|
| `A _Clos network_ is a kind of multistage circuit switching network.` | `A **Clos network** is a kind of multistage circuit switching network.` |
| `Use the word _and_ instead.` | `Use the word "and" instead.` |
| `To form a possessive of a singular noun, add _'s_ to the end.` | `To form a possessive of a singular noun, add **'s** to the end.` |

## Mathematical notation

Mathematical symbols use HTML entities rather than keyboard characters, so assistive technology reads them correctly: `&minus;` for a minus sign, `&times;` for multiplication, `&ne;`, `&le;`, and `&ge;` for the comparisons. Plus, division, and equals keep their keyboard characters. An asterisk never stands in for multiplication in text, though you can drop the multiplication symbol where `ab` stays unambiguous.

Formatting splits by role. Operators take a nonbreaking space on each side and never take italics. Variables always take italics. Short expressions and equations run inline with the text, with nonbreaking spaces holding their components on one line, and an expression that breaks awkwardly moves to its own line. Exponents use `<sup>` and subscripts use `<sub>`, never a caret. Fractions become decimals where possible.

Notation can replace words in running text where it reads cleanly, as in `Check whether a > b`. Where the notation makes the sentence ambiguous, ungrammatical, or hard to read, the words come back.

Complex or multiline equations outgrow HTML entities, and belong in a diagram, an image, or a dedicated math renderer.

| Recommended | Not recommended |
|---|---|
| `a &minus; b` | `a - b` |
| `2<sup>3</sup>` | `2^3` |
| `_x_ &ne; _y_` | `x != y` |
| `Check whether a > b.` | `Check whether a is greater than b.` |
| `The area is calculated by multiplying the length by the width.` | `The area is calculated by multiplying l × w.` |
