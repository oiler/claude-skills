# Language and grammar

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: person, voice, tense, articles, capitalization, contractions, pronouns, sentence-structure, abbreviations, possessives, prepositions, pluralization, reference-verbs

## Second person

Address the reader in the second person. Use `you` and `your` rather than `we`, `our`, and `us`. Assume the reader is the person doing the tasks and making the decisions, and reserve the word `user` for the user of the software your reader is building. When you tell the reader to act, use the imperative; the `you` goes unsaid. Imperative sentences in running text are fine once you have established who you're addressing, though a run of them usually wants to be a numbered procedure instead.

Second person covers what the reader does. Use the third person for what the software or an end user does. First-person plural is acceptable for the organization that authors the document, provided the antecedent is unmistakable, and it also fits the questions in a FAQ or a signed commentary. Identify who the reader is (a developer? an administrator?) and stay consistent about it.

The checker's `first-person` rule reports `we`, `our`, `us`, and `let's` as errors. It skips double-quoted spans and blockquotes so that quoting the guide, which writes in the first person about itself, doesn't trip it.

| Recommended | Not recommended |
|---|---|
| `The following sections describe how you can create a website.` | `The following sections describe how we can create a website.` |
| `Consider adding a description to your table.` | `Let's add a description to our table.` |
| `This document shows you how to develop an app for your organization.` | `This document shows the user how to develop an app for their organization.` |
| `Click Submit.` | `You should now click the Submit button.` |
| `Example Organization provides A and B, but we don't provide C and D.` | `We provide A and B, but not C and D.` |

## Active voice

Use active voice, where the grammatical subject performs the action, and make clear who's performing it. Passive constructions let the actor vanish, which leaves the reader guessing whether the work belongs to them, the server, the client, or an end user. Naming the actor with `by` is possible but usually worse than recasting the sentence.

The guide keeps three exceptions, and the `passive` rule is a warning rather than an error for exactly that reason. Passive is fine to emphasize an object over an action, to de-emphasize an actor you don't want to blame, and where the reader has no reason to care who acted.

| Recommended | Not recommended |
|---|---|
| `Send a query to the service. The server sends an acknowledgment.` | `The service is queried, and an acknowledgment is sent.` |
| `Send a query to the service. The server sends an acknowledgment.` | `The service is queried by you, and an acknowledgment is sent by the server.` |
| `The file is saved.` | `Some process saved the file at some point.` |
| `Over 50 conflicts were found in the file.` | `You created over 50 conflicts in the file.` |

## Present tense

Present tense covers general behavior that isn't tied to a particular moment. Future tense earns its place only when an action genuinely happens later, such as an archive that runs at the next backup or an asynchronous message that reaches subscribers after the call returns. Don't use future tense for how a product works after the next release; that's a timeless-documentation problem. Avoid the hypothetical `would` as well.

| Recommended | Not recommended |
|---|---|
| `Send a query to the service. The server sends an acknowledgment.` | `Send a query to the service. The server will send an acknowledgment.` |
| `Add the filename to the backup list. The file will be archived the next time the backup process runs.` | `Add the filename to the backup list. The file is archived.` |
| `A message is sent that will notify any Pub/Sub subscribers.` | `A message is sent that notifies any Pub/Sub subscribers.` |
| `If you send an unsubscribe message, the server removes you from the mailing list.` | `You can send an unsubscribe message. The server would then remove you from the mailing list.` |

## Articles

Keep the definite and indefinite articles: `a`, `an`, and `the`. Dropping them for brevity costs comprehension and makes translation harder, and the rule holds in headings and titles too. Which indefinite article to use in front of an abbreviation follows pronunciation rather than spelling, so the guide's word list settles the awkward cases.

| Recommended | Not recommended |
|---|---|
| `Create a VM instance` | `Create VM instance` |
| `Set the value of the timeout field.` | `Set value of timeout field.` |

## Capitalization

Follow standard American English capitalization, then stop. Don't capitalize a word without a reason, and don't lean on capitalization to carry meaning: a reader new to the domain won't catch that a capitalized `Pod` means a Kubernetes unit while a lowercase `pod` means anything else. All-uppercase belongs to official names, always-capitalized abbreviations, and quoted code. Camel case belongs to official names and code.

Sentence case is the default everywhere else. Titles and headings take sentence case with no trailing period, and so do captions, image labels, list items, glossary definitions, and every element of a table. References to another document's heading also take sentence case even when the original used title case, so the reference still matches after someone updates the original. Text after a colon starts lowercase unless it's a proper noun, a heading, a quotation, or the text after a label such as `Caution`. Don't name a casing style; state the requirement and show an example.

The `headings` rule reports a heading that ends in a period, and one that looks like title case, as errors.

| Recommended | Not recommended |
|---|---|
| `Set up a service account` | `Set Up A Service Account.` |
| `Open source software: Hadoop` | `Open source software: hadoop` |
| `Note: The quota resets every hour.` | `Note: the quota resets every hour.` |
| `Enter the value with no spaces between words and the first letter of each word capitalized, for example, AssertionAccount.` | `Enter the value in camel case.` |

## Contractions

The guide recommends contractions. Google documentation takes an informal tone, so common two-word contractions such as `you're`, `don't`, and `there's` are the preferred form, not a lapse. Negation contractions carry a specific argument, which the guide states directly: "It's easy for a reader to miss the word not when they're scanning, whereas it's harder to misread don't as do." When the negative genuinely needs emphasis, formatting handles it better than expansion.

Two forms are out. Nonstandard contractions such as `guides're`, and a noun plus `'s` standing in for `is` such as `browser's ready`, aren't standard English. Neither are three-word contractions such as `mightn't've`.

The `contractions` rule enforces that shape of the rule, not the intuitive inversion of it. It flags the nonstandard forms, the noun plus `'s`, and the three-word forms, and it nudges an uncontracted negation toward the contracted form. Ordinary pronoun contractions pass untouched. Every finding is a warning, because contraction is a register choice a house style may override.

| Recommended | Not recommended |
|---|---|
| `The file doesn't exist yet.` | `The file does not exist yet.` |
| `You can't set both fields.` | `You cannot set both fields.` |
| `The guides are up to date.` | `The guides're up to date.` |
| `The browser is ready.` | `The browser's ready.` |
| `The job might not have finished.` | `The job mightn't've finished.` |

## Pronouns

Every pronoun needs an unmistakable antecedent. Vague reference is the common failure: a stray `it` that could point at either of two nouns costs the reader a re-read. Follow a demonstrative such as `this` or `these` with the noun it stands for.

Use the singular `they` as the gender-neutral pronoun. Don't press `he`, `him`, `his`, `she`, or `her` into gender-neutral service, and don't reach for punctuational workarounds such as `he/she` or `(s)he`. The `gendered` rule reports those constructions as errors and cites the `pronouns` page. The role nouns it also flags are a workshop extension of the guide's inclusive-language principle rather than text from that page.

Keep the optional pronouns `that` and `which` when they remove ambiguity. They aren't interchangeable: `that` introduces a restrictive clause and takes no comma; `which` introduces a nonrestrictive clause and takes one. Use `who` for a person, and `whose` for people, animals, and things alike.

| Recommended | Not recommended |
|---|---|
| `If you type text in the field, the text doesn't change.` | `If you type text in the field, it doesn't change.` |
| `Set this value to true.` | `Set this to true.` |
| `These approaches are your best options.` | `These are your best options.` |
| `Ask the developer whether they finished the migration.` | `Ask the developer whether he/she finished the migration.` |
| `Right-click the link that you want to open.` | `Right-click the link you want to open.` |
| `The echidna, which has a long snout, is furry.` | `The echidna which has a long snout is furry.` |

## Sentence structure

Put the circumstance, condition, or goal before the instruction. A reader who meets the condition first can skip an instruction that doesn't apply to them; a reader who meets the instruction first has already started following it. The `condition-order` rule reports a procedural step whose `if`, `when`, or `unless` arrives after the verb, as a warning.

| Recommended | Not recommended |
|---|---|
| `For more information, see [link to other document].` | `See [link to other document] for more information.` |
| `To delete the entire document, click Delete.` | `Click Delete if you want to delete the entire document.` |
| `If your app is in one of the following regions, custom domains might add noticeable latency to responses:` | `Using custom domains might add noticeable latency to responses if your app is in one of the following regions:` |

## Abbreviations

Abbreviations cover acronyms, initialisms, shortened words, and contractions. The technical split between an acronym and an initialism rarely matters, so `acronym` covers both. Spell out an unfamiliar term on first mention with the abbreviation in parentheses, italicize both, and capitalize the spelled-out form only when it's a proper noun. After that, the abbreviation stands alone. Some abbreviations rarely need expansion: `AI`, `API`, `DVD`, `HTML`, `PC`, `RAM`, `REST`, `URL`, `USB`, file formats, and units of measurement. Some gain nothing from expansion; `portable document format` teaches nobody what a `PDF` is.

Mechanics:

- Skip the periods in acronyms and initialisms.
- Keep a period on a shortened word. Date and time abbreviations are the exception, and so is a short form you speak as a word.
- Abbreviations for country names, state names, and the District of Columbia take no periods.
- Don't use an abbreviation as a verb.
- Don't use internet slang such as `tl;dr` or `ymmv`.
- Spell out symbols that stand in for words.

Two Latin abbreviations carry corrected facts. The guide bans `i.e.` and `e.g.` outright: write `that is` and `for example`. `etc.` is the weaker case, acceptable in some circumstances but better rephrased in most lists. The `latin` rule encodes both severities. It reports `i.e.` and `e.g.` as errors, `etc.` as a warning, and it also warns on `via` and `vs.` from the word list. The `acronyms` rule separately warns about an acronym that appears without an expansion.

| Recommended | Not recommended |
|---|---|
| `Border Gateway Protocol (BGP)` | `BGP, the border gateway protocol` |
| `data manipulation language (DML)` | `Data Manipulation Language (DML)` |
| `The internet of things (IoT) service can connect to sensors in low Earth orbit.` | `The IoT (internet of things) service can connect to sensors in LEO (low Earth orbit).` |
| `that is` | `i.e.` |
| `for example` | `e.g.` |
| `Use SSH to log in to your remote shell.` | `Then ssh into your remote shell.` |
| `Updating the software made throughput 10 times faster.` | `Updating the software made throughput 10x faster.` |

## Possessives

For a singular noun, including one ending in `s`, add `'s`. For a plural noun ending in `s`, add the apostrophe alone. For a plural noun not ending in `s`, add `'s`. When the possessive reads awkwardly, rewrite the sentence without it.

Product, feature, and company names take a different rule. Don't form a possessive from a feature name, product name, or trademark when you're describing function or performance; use the name as a modifier, or rewrite with `of`. A company name takes `'s` for ordinary possession, but not when the name is doing trademark duty. Don't form the possessive of a code item either. Take the possessive from the noun after it, or rewrite around it. And don't use `'s` to form a plural.

| Recommended | Not recommended |
|---|---|
| `Raise the storage class's quota.` | `Raise the storage classes quota.` |
| `Extend the models' capabilities.` | `Extend the models's capabilities.` |
| `Analyze the business data.` | `Analyze the businesses' data.` |
| `The rule that the Federal Trade Commission (FTC) issued.` | `The Federal Trade Commission's (FTC's) rule.` |
| `You can use this template to monitor Google Search performance.` | `You can use this template to monitor Google Search's performance.` |
| `Compare the number to the wordCount method's return value.` | `Compare the number to wordCount's return value.` |

## Prepositions

No rule forbids a preposition at the end of a sentence. Put the preposition where the sentence reads best, even if that's the end. Include the prepositions that add clarity, drop the ones that add nothing, and don't stack so many that the sentence turns to mush.

| Recommended | Not recommended |
|---|---|
| `For details, see the client library documentation for the language you're interacting with.` | `For details, see the client library documentation for the language with which you're interacting.` |

## Pluralization

Follow standard American English pluralization, and don't use `'s` to form a plural, which blurs the plural against the possessive and the contraction. Match the verb to the real subject in a long or complex sentence. Two subjects joined by `and` take a plural verb; two joined by `or` agree with the nearer one. Use a plural after `one or more`, and a singular after `more than one`.

Abbreviations pluralize like ordinary words: add `s`, or `es` after `s`, `sh`, `ch`, or `x`. A spelled-out term and its abbreviation match in number. A unit abbreviation after a number stays singular. Spelled-out units take the singular only for exactly one. Every other number takes the plural, including zero, decimals, and values above one.

Don't put optional plurals in parentheses. Pick the singular or the plural and stay consistent; when both genuinely matter, write `one or more`. The `optional-plurals` rule reports the parenthetical form as an error.

| Recommended | Not recommended |
|---|---|
| `Confirm that the number of entries listed in the directory is accurate.` | `The efficiency of algorithms that process data sets depend on memory allocation.` |
| `The request payload and header information are logged for debugging.` | `User authentication and authorization is processed by the security module.` |
| `If one or more tests fail, a system warning is triggered.` | `If one or more test fails, a system warning is triggered.` |
| `APIs, SKEs, and IDEs` | `API's, SKE's, and IDE's` |
| `virtual machines (VMs)` | `virtual machines (VM)` |
| `64 GB` | `64 GBs` |
| `To find your API key, visit the Credentials page.` | `To find your API key(s), visit the Credentials page.` |
| `You can use a physical linecard, which can contain one or more ports.` | `You can use a physical linecard, which can contain port(s).` |
| `Intent objects and Activity instances` | `Intents and Activitys` |

## Verbs in reference documents

In reference documentation for a method, describe what the method does rather than what a developer would use it to do. The distinction shows up as a single letter: the third-person `-s` ending on the leading verb.

| Recommended | Not recommended |
|---|---|
| `tasks.insert: Creates a new task on the specified task list.` | `tasks.insert: Create a new task on the specified task list.` |
