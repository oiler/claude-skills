# Voice and tone

Source: Google developer documentation style guide, https://developers.google.com/style — pinned to the guide's last update, 2026-07-07. Mirrored 2026-08-18.

Adapted from the Google developer documentation style guide, licensed under CC BY 4.0.

Pages distilled here: tone, anthropomorphism, excessive-claims, jargon, timeless-documentation, future, prescriptive-documentation, other-sources

## Voice and tone

Aim for a voice that's conversational, friendly, and respectful, without slang and without being frivolous. The guide's own target: "Try to sound like a knowledgeable friend who understands what the developer wants to do." Don't write the way you speak, because speech is more colloquial and more verbose than developer documentation should be, but stay closer to conversation than to formality. Readers come from many cultures and read English at many levels. Drop culturally specific references and pop-culture jokes; simple, consistent writing also translates better.

What to cut:

- Buzzwords and technical jargon.
- Cutesiness, wackiness, and goofiness.
- Figurative language, including metaphors.
- Ableist language.
- Placeholder phrases such as `please note` and `at this time`.
- Choppy sentences. Long-winded ones too.
- A run of sentences that all open the same way.
- Exclamation marks.
- Phrasing in terms of `let's do something`.
- Internet slang and internet abbreviations.
- Phrasing that denigrates or insults any group of people.

Politeness is good, but `please` in a set of instructions is overdoing it, and the checker's `please` rule reports it as an error.

| Recommended | Not recommended |
|---|---|
| `To view the document, click View.` | `To view the document, please click View.` |
| `For more information, see [link to other document].` | `For more information, please see [link to other document].` |
| `This API lets you collect data about what your users like.` | `Dude! This API is totally awesome!` |
| `To clean up, call the collectGarbage method.` | `Then—BOOM—just garbage-collect, and you're golden.` |
| `To get the user's phone number, call user.phoneNumber.get.` | `The telephone number can be retrieved by the developer via the simple expedient of using the get method on the user object's phoneNumber property.` |

## Anthropomorphism

Don't attribute human qualities to software or hardware. Anthropomorphism is a category of figurative language: less precise than direct language, and harder to understand and to translate. The `anthropomorphism` rule flags a software noun such as `system`, `API`, `service`, or `browser` followed by a verb of wanting, knowing, or deciding, and reports it as a warning, because the fix is a rewrite rather than a substitution.

| Recommended | Not recommended |
|---|---|
| `A Delimiter object specifies where to split a string.` | `A Delimiter object tells the splitter where a string should be broken.` |
| `The PC detects a new device.` | `The PC sees a new device.` |

## Excessive claims

An excessive claim asserts something about performance or cost that the reader can't verify from available data, something about security that a single incident would invalidate, or something subjective or disparaging about a third-party product. Judge every claim against what might be true later, not only what's true today.

Avoid superlatives such as `best`, `simplest`, `fastest`, `never`, and `always`. Use `ensure` and `guarantee` only for outcomes the product genuinely delivers. Cite the source of any specific performance number. Write that a security feature `helps with security` or `is designed for security`; those sentences stay true even after an incident. The safest approach is to write factually and objectively, limited to information that stays verifiable across the document's lifespan.

The checker's `excessive-claims` rule is narrower than the page and cites a different one. It flags reader-belittling words such as `simply`, `easily`, `obviously`, and `clearly`, which the guide attests in its word list rather than here, so the rule's page is `word-list`.

| Recommended | Not recommended |
|---|---|
| `Our product distributes datasets and computation in memory across a cluster, and therefore it can be faster for this scenario than ExampleCorporation's product. For more information, see Performance comparison.` | `Our product is faster than ExampleCorp's product.` |
| `Using our security product is part of an overall strategy that helps prevent account takeovers from phishing attacks.` | `Our security product prevents account takeovers from phishing attacks.` |

## Jargon

Jargon is the specialized, often figurative terminology of a specific group standing in for a larger concept: terms such as `camel case`, `swim lane`, `break-glass procedure`, and `out-of-the-box`, plus vague, overloaded words such as `solution`, `support`, and `workload`. Outside the group the meaning doesn't carry, which works against clear content, translation, readers at different levels of product knowledge, and inclusion.

Some jargon is worth keeping, because readers search for it. Before you keep a term, work down four questions. Can you write around it? Can you replace it with a more specific term, the way the word list offers `affected area` for `blast radius` and `import` for `ingest`? Do you use it once, in which case describe it in plain language and put the jargon in parentheses or link to a trusted definition? Do you use it throughout, in which case define it in parentheses on first reference? A term used in a command or code sample stays in code font, in direct reference to the code item.

| Recommended | Not recommended |
|---|---|
| `When the project is finished, review what processes worked or didn't work.` | `Hold a post-mortem.` |
| `Use an informal design process.` | `Create a back-of-the-envelope design.` |
| `The application is in the same state as a cold standby (a backup or redundant system that's identical to a primary system).` | `The application is in the same state as a cold standby.` |
| `Add a user to the allowlist (whitelist) by entering the following: whitelist adduser EMAIL_ADDRESS.` | `Add a user to the whitelist by entering the following: whitelist adduser EMAIL_ADDRESS.` |

## Timeless documentation

Timeless documentation avoids words that anchor a page to its publication date or that assume knowledge of earlier or later versions. Document the current version, describing how the product works rather than how it changed or how it might change. Two payoffs: less maintenance, and no assumption that the reader knew the previous release.

The words that undermine timelessness are the ones that promise plans (`at present`, `as of this writing`, `eventually`), the ones the documentation's own existence already implies (`currently`), the ones that expire on publication (`soon`, `latest`), and the ones that assume prior knowledge (`new`, `newer`, `old`, `older`, `existing`, `now`). Pair a necessary `new` with a reference point such as a date or a release number.

The `future` rule enforces the sharpest edge of this, reporting `currently`, `at this time`, `as of this writing`, `at present`, `for now`, `will soon`, `coming soon`, `in a future release`, and `in an upcoming release` as errors. The guide's exception is time-stamped content: release notes, blog posts, and press releases may use these words, and so may a procedure describing a change of state after a step.

| Recommended | Not recommended |
|---|---|
| `These subcommands let you interact with HTTP load balancing.` | `These new subcommands let you interact with HTTP load balancing.` |
| `The following command-line options aren't supported:` | `The following command-line options aren't currently supported:` |
| `The emulator supports the following filters:` | `The emulator now supports the following filters:` |
| `The January 14, 2021 release of BigQuery includes a new resource panel.` | `BigQuery includes a new resource panel.` |

## Future features

Don't document future features or products, even in innocuous ways. Nothing gets pre-announced in documentation unless legal counsel has approved it. The `future` rule catches the usual phrasings, but treat the rule as a net rather than the policy itself: the policy is that unshipped work stays out of the documentation, whatever the wording.

| Recommended | Not recommended |
|---|---|
| `Cloud Storage supports the following storage classes.` | `Cloud Storage will soon support a fourth storage class.` |
| `The API returns a JSON payload.` | `In a future release, the API returns a protocol buffer payload.` |

## Prescriptive documentation

Prescriptive, or opinionated, documentation recommends a way to accomplish the task instead of handing the reader a list of options to choose from. When a goal involves several approaches or products, it recommends a path. That commitment shapes three things: the document's purpose and structure, the scenarios it picks, and the sample commands it prints, which should accomplish the most common use case.

Auxiliary verbs carry the prescription. `must` marks a required action, `can` an optional one, and `might` a possible outcome. Generally avoid `should`, which leaves the reader unsure whether an action is required or merely suggested; the guide allows it for a generally recognized recommendation, such as "You should use a strong password." The phrases "We recommend" and "Google recommends" state a recommended action plainly. When you describe a state, say who sets the value rather than what the value ought to be.

| Recommended | Not recommended |
|---|---|
| `Ensure that the Classroom Share Button conforms to our min-max size guidelines and related color and button templates.` | `The Classroom Share Button should conform to our min-max size guidelines and related color and button templates.` |
| `The column of the data table that the filter operates on.` | `The column of the data table that the filter should operate on.` |
| `Whether it's a brand new project or an existing one, perform the following steps.` | `Whether it's a brand new project or an existing one, here's what you should do.` |
| `You must set the value to true.` | `The value should be true.` |

## Third-party content

Don't copy content from another source, because doing so might violate copyright. Paraphrase it and link to the original instead. Content covers text, images, code, logos, and speech.

Unless you're sure your company owns the assets, avoid copying from third-party sources such as documentation, websites, books, blogs, videos, images, and podcasts; from reference sources such as dictionaries, encyclopedias, and Wikipedia; from open source product documentation, whose licenses run from no reuse without attribution to complete freedom; and from GitHub, where each user picks their own license. When in doubt, don't use it.

| Recommended | Not recommended |
|---|---|
| `A recovery point objective (RPO), which is the maximum acceptable length of time during which data might be lost from your app due to a major incident.` | `Recovery Point Objective (RPO): "RPO is the maximum targeted period in which data (transactions) might be lost from an IT service due to a major incident" (https://en.wikipedia.org/wiki/Disaster_recovery).` |
