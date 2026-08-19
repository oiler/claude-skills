<!-- GENERATED FILE — do not edit. Source: scripts/data/word_list.json.
     Regenerate with: python3 scripts/gen_word_list.py -->

# Word list

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

The `word-list` rule in `scripts/style_check.py` flags every term below. This page holds the 40 entries the checker enforces mechanically; the guide's full word list is much longer and lives at https://developers.google.com/style/word-list.

## Don't use these

The checker reports each of these as an error.

| Term | Use instead | Why |
|---|---|---|
| `a number of` | several, many, or the actual number | Vague quantity. Give the reader the number when you know it. |
| `abort` | stop, cancel, or halt | Violent and imprecise. Name the action that actually happens. |
| `allows you to` | lets you | Shorter, and the product is not granting permission. |
| `and/or` | or, or name both cases | Ambiguous and hard to translate. Write out the cases you mean. |
| `at this point in time` | now, or cut the phrase | Padding. |
| `blacklist` | denylist or blocklist | Non-inclusive. The replacement is also more literal. |
| `desire` | want | Plain word. |
| `dummy` | placeholder, sample, or example | Non-inclusive and vague. |
| `functionality` | features, capabilities, or behavior | Abstract noun standing in for a specific one. |
| `grayed out` | unavailable or dimmed | Describes appearance, not state, and fails for readers who cannot see it. |
| `greyed out` | unavailable or dimmed | Also the non-American spelling. |
| `hit` | press, click, or call | Name the real interaction. |
| `in order to` | to | Two words of padding in front of every purpose clause. |
| `in the event that` | if | Padding. |
| `kill` | stop, cancel, or end | Violent. The exception is a literal `kill` command in code font, which the checker already ignores. |
| `leverage` | use | Business jargon for a plain verb. |
| `prior to` | before | Plain word. |
| `slave` | replica, secondary, or worker | Non-inclusive. |
| `subsequent to` | after | Plain word. |
| `terminate` | stop or end | Plain word. |
| `under the hood` | internally, or describe the mechanism | Idiom that does not translate. |
| `utilize` | use | Longer word, same meaning. |
| `whitelist` | allowlist | Non-inclusive. The replacement is also more literal. |
| `wish` | want | Plain word. |

## Use this form instead

One spelling or construction is correct; the other is reported as an error.

| Term | Use instead | Why |
|---|---|---|
| `backwards compatible` | backward compatible | No trailing s on the adjective. |
| `check the checkbox` | select the checkbox | Google's interaction verb for a checkbox is select, and clear for the reverse. |
| `click on` | click | You click a button, not on it. |
| `drop down` | drop-down list | Hyphenated as a modifier, and it needs the noun it modifies. |
| `e-mail` | email | One word, no hyphen. |
| `info` | information | Spell it out outside UI labels. |
| `irregardless` | regardless | Not a word. |
| `login to` | log in to | Two words as a verb. One word as a noun or adjective. |
| `type in` | enter | Enter covers typing, pasting, and dictating. |
| `uncheck` | clear | Google's verb for clearing a checkbox. |
| `web site` | website | One word. |

## Use with care

Acceptable in a narrow context, reported as a warning so you can judge.

| Term | Use instead | Why |
|---|---|---|
| `as a service` | spell out the offering | Marketing shorthand. Fine in a product name, weak in prose. |
| `execute` | run | Fine for a program executing an instruction; use run for what the reader does. |
| `master` | primary, main, or original | Non-inclusive in `master`/`slave` pairings. A git branch named `master` is a literal name and belongs in code font. |
| `native` | built-in, integrated, or the platform's name | Ambiguous and carries a second meaning about people. |
| `repo` | repository | Spell it out on first use in reference material. |
