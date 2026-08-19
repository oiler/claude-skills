# Code and user interface

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: code-in-text, code-samples, code-syntax, placeholders, ui-elements, api-reference-comments, filenames, text-formatting

## Code in text

Code font does three jobs in a sentence: it signals that the reader types the text verbatim, it shows the boundaries of that text, and it separates the entity from the prose around it. HTML marks it with the `code` element, Markdown marks it with backticks. Almost anything to do with code takes it: attribute names, attribute values, class names, command output, data types, database elements, defined constants, DNS record types, element names, enum names, environment variables, filenames, file paths, folders, HTTP content types, HTTP status codes, HTTP verbs, `IAM` role names, IP addresses, language keywords, method names, function names, namespace aliases, package names, port numbers, query parameters, placeholder variables, strings used in commands, and text the reader enters.

Three kinds of thing stay in ordinary font: domain names, the name of a product, a service, or an organization, and URLs the reader follows in a browser. Three more are conditional. A Boolean takes code font as a literal value and ordinary font as the evaluation of a condition. A command-line utility name takes code font while the project or product of the same name doesn't, which makes `gcloud` code font with Google Cloud CLI plain. An email address takes code font when it's input or output, and ordinary font with a link when it's a way to reach someone. A UI element that also qualifies for code font takes both code font and bold.

Code elements don't decline like English words. Don't pluralize or make a code name possessive; add a noun after it and inflect the noun, so `the ADDRESS constant's value` rather than the constant's own name carrying the apostrophe. Don't verb them either: send a `POST` request rather than posting the data. Refer to a method without its class name unless the class prevents ambiguity. A status code is a status code, never a response code or an error code, with the number and name in code font, `Nxx` for a whole range, and `HTTP` droppable when context supplies it. Quotation marks don't go around code unless the code contains them.

| Recommended | Not recommended |
|---|---|
| ``The `SnapshotDiskOperator` class includes the `generate_snapshot_name` method.`` | `The SnapshotDiskOperator class includes the generate_snapshot_name method.` |
| ``The `ADDRESS` constant's value is defined in the `settings.h` file.`` | ``` `ADDRESS`'s value is defined in `settings.h`. ``` |
| `To add the data, send a POST request.` | `POST the data.` |
| `an HTTP 400 Bad Request status code` | `a 400 response code` |
| `call its get method` | `call its animal.get method` |
| `You can find support at https://support.example.com.` | ``You can find support at `https://support.example.com`.`` |

## Code samples

A code sample follows the indentation rules of its language's style guide, which for most languages means spaces rather than tabs and two spaces per level. Lines wrap at 80 characters, or fewer where the reader is likely to have a narrow window or to print the page. HTML marks the block with `pre`, Markdown indents every line by four spaces or fences the block. Mark omitted code with a comment in the sample's own language, never with three dots or the ellipsis character, and don't offer a block containing an omission as click-to-copy.

Introduce a code sample with a sentence or a paragraph. The introduction ends with a colon when the sample follows immediately, and with a period when other material sits between them or when the introduction's last sentence isn't about the sample. That last case is the one writers get wrong: a lead-in that ends by pointing at a link, and then ends with a colon, promises the sample but delivers a cross-reference.

| Recommended | Not recommended |
|---|---|
| `The following code sample shows how to use the get method:` | `The following code sample shows how to use the get method. For more information, see [link]:` |
| `# Several lines of code are omitted here.` | `...` |
| `Wrap lines at 80 characters.` | `Let the line run as long as the code needs.` |

## Command-line syntax

Documentation for a command links to the command reference inline, usually from the sentence that introduces the command. Keep the number of arguments small and let the reference carry the full list. The example a reader copies should run without editing, which means it holds only runnable code and placeholders.

Formatting a long command has a fixed shape. Break a line past 80 characters before a hyphen, a double hyphen, an underscore, or a quotation mark, and indent every continuation four spaces so the lines align. Every line except the last ends with the continuation character for its shell, which on Linux and Cloud Shell is a space followed by a backslash, and on Windows a space followed by a caret. A command missing that character doesn't run. A list after the command explains its placeholders. An option description takes end punctuation when it's a complete sentence and none when it's a single word or a noun phrase, unless the list mixes both.

Show the prompt symbol on every line of a multi-line input block, and never show the directory path before the prompt, though a changed context such as moving to a remote machine earns a new prompt indicator. On a one-line command the prompt is optional, though a document holding one-line commands alongside multi-line ones uses it throughout. Input and output belong in separate code blocks.

Three notations mark argument shapes, and all three break a click-to-copy command, so keep them out of one. Square brackets mark an optional argument, with each optional item in its own pair. Curly braces with pipes mark a set of mutually exclusive choices, exactly one of which the reader picks. Three dots with no spaces mark an argument the reader can repeat. Where a command needs one of these, drop the optional arguments, give each option its own code block, or split the options into separate tasks.

| Recommended | Not recommended |
|---|---|
| `gcloud dns GROUP [GLOBAL_FLAG] [FILENAME]` | `gcloud dns GROUP [GLOBAL_FLAG FILENAME]` |
| `{FILE_1\|FILE_2}` | `FILE_1 or FILE_2` |
| `gcloud dns GROUP [GLOBAL_FLAG ...]` | `gcloud dns GROUP [GLOBAL_FLAG . . .]` |
| `gcloud compute images import IMAGE_NAME \` | `gcloud compute images import IMAGE_NAME` |

## Placeholders

A placeholder stands for a value the reader replaces, and its default value is a descriptive name. Placeholder text is uppercase with underscores between words: `API_NAME`, `METHOD_NAME`. Never `API-name`, `api_name`, or `apiName`. A possessive adjective doesn't belong in one, which rules out `MY_API_NAME` and `YOUR_API_NAME`. A single `x` or a run of them isn't informative enough to be a placeholder, with the standing exception of HTTP status code ranges, where `xx` is the convention. Where uppercase with underscores would be wrong for the context, pick something else, then stay internally consistent.

Markup depends on where the placeholder sits. HTML wraps it in `var`, and in a code block that `var` sits inside `pre`. Markdown wraps an inline placeholder in backticks with an asterisk outside each one, and a code fence can't carry any formatting at all, so a placeholder inside a fence is plain uppercase text. Brackets, braces, and ellipses that mark argument shape stay outside the `var` element.

Explain a placeholder the first time it appears, and again later only where the document is long, the procedure introduced several others, or the reader is unlikely to read from the top. One placeholder gets the form `Replace PLACEHOLDER with a description of what the placeholder represents`. Two or more get a list introduced by `Replace the following:`, in the order they appear in the command, each entry a placeholder, a colon, and a description starting lowercase. Introduce an example inside a description with an em dash or with `such as`. Placeholders in sample output follow the same shape under the lead-in `This output includes the following values:`.

| Recommended | Not recommended |
|---|---|
| `PROJECT_ID` | `project-id` |
| `INSTANCE_NAME` | `YOUR_INSTANCE_NAME` |
| `Replace BUILD_ID with the ID of the build that you copied.` | `Replace the placeholder with your own value.` |
| `LOCATION: the location of the reservation` | `LOCATION: The location of the reservation.` |

## UI elements and interaction

State an instruction as what the reader accomplishes rather than which widget they touch, where that stays clear. `Refresh the page` outlives a redesign that `Click the circular arrow` doesn't. Where the point of the procedure is navigating the interface, or the element is genuinely hard to find, describe the element.

A UI element referred to by name goes in bold, with `b` in HTML or double asterisks in Markdown, and that covers buttons, menus, dialogs, windows, list items, and anything else on the page carrying a visible label. Don't use quotation marks around the label and don't use code font for it, unless the element separately qualifies for code font, in which case it takes both. Follow the capitalization shown on the page, except that an all-uppercase label becomes sentence case, as does a set of inconsistently cased labels. A product or feature name takes bold only when it names an element on the page.

The terms are specific, and the guide holds them apart. A window is an application window or a modular element you can open and close; a page is a webpage or a console subpage; a dialog is a smaller detached window in front of the main one; a pane or panel is a rectangular region inside a larger window; a section is a labeled grouping of controls inside one of those. A menu holds commands, not choices or options or menu items. A navigation menu isn't a navigation bar or pane. A toolbar holds buttons, one of which may be a menu button. A checkbox, a radio button, an expander arrow, a toggle, a text box, a list box, a combo box, and a spin box each have their own name, and slang like `zippy` or `hamburger icon` isn't one of them. In Google Cloud and Google Workspace documentation, the word for a text box is field.

Interaction verbs are where the `word-list` rule does its enforcement, and all four entries are errors. You `click` a button, not `click on` it. You select a checkbox rather than `check the checkbox`, and you clear one rather than `uncheck` it. You enter a value rather than `type in` one, because entering covers typing, pasting, and dictating alike. Beyond those, `press` is for a key that triggers an action, `type` or `enter` for a key typed as text, and `toggle` is never a verb: name the state you want the reader to reach.

Accessibility constrains the rest. Don't orient the reader with `above`, `below`, or `right-hand side`; use the button's icon with its tooltip name, add context such as the toolbar it sits on, or show a screenshot. An icon without a tooltip is a bug worth filing, because the tooltip is what a screen reader announces. An angle-bracket sequence takes a nonbreaking space before each bracket, one bold span around the whole sequence, and an `aria-label` of `and then` on the bracket so a screen reader doesn't say "greater than." Keyboard keys use the `kbd` element, letter keys in uppercase, modifier names spelled out rather than symbols, in the form `Control+Shift+K`, with the macOS shortcut in parentheses after the Windows and Linux one. Drop a trailing ellipsis from a UI label.

| Recommended | Not recommended |
|---|---|
| `Click Save.` | `Click on the Save button.` |
| `Select the Bookmarks checkbox.` | `Check the Bookmarks checkbox.` |
| `Clear the Bookmarks checkbox.` | `Uncheck the Bookmarks checkbox.` |
| `In the Name field, enter an account name.` | `Type in an account name.` |
| `In the New project window, select the New activity checkbox.` | `In the New Project window, select "New Activity".` |
| `To copy, press Control+C (or Command+C on macOS).` | `To copy, press Ctrl+c.` |
| `Click Browse.` | `Click Browse ....` |
| `To expand the Advanced options section, click the expander arrow.` | `Click the zippy.` |

## API reference code comments

An API reference describes every class, interface, and struct; every constant, field, enum, and typedef; and every method, including each parameter, the return value, and every exception it throws. Each reference page opens with a code sample of roughly five to twenty lines. API names, classes, methods, constants, and parameters go in code font and link to their reference pages. String literals go in code font inside double quotation marks. Spell a class name exactly as the code spells it, and never pluralize it: add a noun and pluralize that, giving `Intent objects` rather than `Intents`.

Descriptions follow a fixed opening by kind, because generators cut the summary at the first period and index only that sentence. A class description states the purpose that the name and signature don't already give, without repeating the class name and without the phrase `this class does`. A method description opens with a verb naming the action: a getter returning a Boolean starts `Checks whether`, any other getter starts `Gets the`, a setter starts `Sets the`, a callback starts `Called by`, and a convenience constructor starts `Creates a`. Everything runs in the present tense.

Parameters and returns have their own forms. A parameter description starts with a capital and ends with a period, and a non-Boolean one opens with `The` or `A`. A Boolean parameter that instructs the API states what happens for each value; a Boolean parameter that reports state uses `True if …; false otherwise.`, with neither word in code font or quotation marks in that context. State a default as `Default:` after the behavior it belongs to. Keep a return value's description as brief as it can be. A value opens with `The …`, and a Boolean uses the same `True if …; false otherwise.` form. An exception starts `If …` where the generator supplies the word `Throws`, and `Thrown when …` where it doesn't. A deprecation names the replacement in its first sentence, and tells the reader what to change.

| Recommended | Not recommended |
|---|---|
| `Adds a new bird to the ornithology list and returns the ID of the new entry.` | `This method will add a new bird.` |
| `Checks whether this activity is being destroyed.` | `Returns a boolean.` |
| `True if the zoom is set; false otherwise.` | ``Returns `true` if the zoom is set.`` |
| `Thrown when no key is assigned.` | `Error case.` |
| `Deprecated. Use #CameraPose instead.` | `Deprecated.` |
| `Intent objects` | `Intents` |

## Filenames

File and directory names are lowercase, separated by hyphens rather than underscores, and built from standard `ASCII` alphanumeric characters. Case matters because most Unix-style systems are case sensitive, so `Impersonate-Service-Accounts.html` names a different file from `impersonate-service-accounts.html`. Hyphens matter because search engines read them as word breaks and generally don't read underscores that way. A generic name such as `document1.html` names nothing. The one standing exception is consistency: a directory already full of underscored names can take another underscored name rather than a lone hyphenated one.

Referring to a file has three parts. Put the name in code font, follow it with the word `file`, and spell it exactly as it is, even where the name breaks the naming guidance. Where the page shows the file's contents, the introduction to that sample names the file. Don't turn a file type into a verb: extract a zip file rather than unzipping it.

Name a file type by its formal name rather than its extension, and expect that formal name to run in all capitals, because many of them are acronyms. A `.png` file is a `PNG` file, a `.sh` file is a Bash file, a `.py` file is a Python file, a `.md` file is a Markdown file, and a `.zip` file is a zip file.

| Recommended | Not recommended |
|---|---|
| `query-data.html` | `query_data.html` |
| `avoiding-cliches.jd` | `avoidingCliches.jd` |
| ``In the following `build.sh` file, modify the default values:`` | `In build.sh, modify the default values:` |
| `a PNG file` | `a .png file` |
| `Extract a zip file.` | `Unzip a zip file.` |

## Text-formatting summary

The guide's own summary page reduces every formatting decision to one table, and this is that table. Two negatives sit underneath it and apply everywhere. Never override global font type, size, or color inline. Never use an ampersand as a conjunction, not in body text, not in a heading, not in a navigation label; the single exception is a UI element or menu whose own name contains one.

| Formatting | What it's for |
|---|---|
| Bold | UI elements and run-in headings, including the label at the start of a notice. In Markdown, use `**`, not `__` |
| Italics | A term you define, a word used as a word, emphasis the sentence can't carry on its own, titles of books, movies, and other full-length works, mathematical variables, and version variables. In Markdown, use `_`, not `*` |
| Underline | Link text, and nothing else |
| Code font | Filenames, class names, method names, HTTP status codes, console output, user input, inline code, and placeholders. `<code>` or a backtick inline, `<pre>` or a fence for a block |
| Placeholder text | `ALL_CAPS` with underscores between words |
| Capitalization | American English generally, and sentence case in every heading, title, and navigation label |
| Quotation marks | American English punctuation, and titles of shorter works such as articles or episodes, unless they're part of a link |
| Ampersand | Don't. Write `and`. The exception is a UI or menu name that itself contains an ampersand |
| Inline font overrides | Don't. Use semantic HTML or Markdown instead of manual styling |
