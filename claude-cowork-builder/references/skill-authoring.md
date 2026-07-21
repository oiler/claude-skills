# Skill authoring — command, knowledge, and router skills

Skills are the primary and near-exclusive capability layer in a Cowork plugin. This reference is technical, decision-dense — it's addressed to you, the operator building the plugin. The skills you emit from it are not: their user-facing copy is read by a nontechnical or light-technical Cowork end user. Keep that split in mind at every step below — a rule here about *how you author* a skill body is not automatically a rule about *what the skill says to its user*. Section-by-section, this doc flags where that split matters.

## The two-tier model

Every skill you author is one of two shapes. Pick one; don't blend them.

**Command skill** — user-facing, invoked deliberately.
- Has `argument-hint` in frontmatter.
- Uses `$1` / `@$1` substitution to consume the invocation argument.
- Appears in the Cowork slash menu as `/skill-name`.

**Knowledge skill** — background, auto-triggered.
- No `argument-hint` — it doesn't take a slash argument.
- Fires when its `description` matches the conversation, not on explicit invocation.
- Set `user-invocable: false` to hide it from the slash menu entirely. A knowledge skill without this flag still auto-triggers, but it also clutters the menu with an entry point that doesn't expect direct invocation — set the flag unless you have a specific reason to leave it invocable.

**The pairing idiom.** The default shape for anything with real depth is a thin command skill paired with a rich knowledge skill: the command skill owns the slash-menu entry, argument handling, and a short dispatch to the knowledge skill; the knowledge skill owns the actual process, references, and detail. This keeps the user-visible surface small (one clean `/command`) while the substance lives somewhere that doesn't compete for slash-menu space. Don't duplicate content across the pair — the command skill delegates, it doesn't restate.

## Router skill — when skill count ≥ 8

Once a plugin's skill count reaches roughly 8 or more, add a router skill: a dispatcher whose only job is an intent→skill routing table. It does no work itself — no generation, no file writes, no domain logic. It reads what the user is asking for, matches it to a row, and hands off to the matching skill.

```markdown
| When the user wants to… | Route to |
|---|---|
| ...intent... | skill-name |
```

Below that threshold, skip it — a routing layer over 3-4 skills is overhead the plugin doesn't need; the plugin's own top-level skill descriptions are enough for auto-trigger and slash-menu discovery to work.

## Frontmatter rules

Cowork skill frontmatter carries exactly four possible fields. Nothing else belongs here — no `allowed-tools`, no `model`; those are Claude Code power-user fields with no equivalent in the Cowork surface.

| Field | Command skill | Knowledge skill |
|---|---|---|
| `name` | required | required |
| `description` | required, third-person, trigger-phrase-rich | required, third-person, trigger-phrase-rich |
| `argument-hint` | present | omit |
| `user-invocable` | omit (defaults true) | `false` |

`description` is written in third person about the skill, not as an instruction to the skill (`"Summarizes meeting notes into action items."` not `"Summarize the meeting notes."`), and it's trigger-phrase-rich: pack in the concrete phrasing a user would actually type, closing with a `Use when…` clause. This is the field that decides whether the skill fires at all — undertriggering is the most common failure mode, so err toward more explicit trigger phrases, not fewer.

## The command-skill body template

Every **command** skill body follows this section order. This is the canonical shape; the command-skill template reproduces it exactly:

```markdown
## Trigger

## Inputs

## Steps

1. ...
2. ...

## Output Format

## After
```

- **`## Trigger`** — one or two lines: what phrasing or situation this skill responds to. Doubles as a sanity check against the skill's own `description`.
- **`## Inputs`** — what the skill needs from the user or the conversation to run. This is also where the standalone/supercharged split lives (below).
- **`## Steps`** — the numbered steps the skill actually executes, in order. This is the only section that's a numbered list; everything else is prose or a table.
- **`## Output Format`** — the shape of what gets produced, concretely enough that two runs of the skill produce comparably-shaped output.
- **`## After`** — a closing menu of next actions the user can take from here (not a sign-off; an actual menu, mirroring the board-menu pattern this builder itself uses).

Don't reorder or drop these sections in a command skill — the command-skill template keys off them being present and in order.

## The knowledge-skill body

Knowledge skills are auto-triggered background material, not user-invoked actions, so they do **not** take the command body shape. Keep them lighter and free-form: a short `## Scope` (what this knowledge covers and when it applies) followed by `## Rules` (the domain facts, constraints, or procedure Claude should follow) — or whatever headings the knowledge actually needs. No `## Steps`, no `## Output Format`, no `## After`; a knowledge skill informs other skills, it doesn't produce standalone output. Set `user-invocable: false` so it stays out of the slash menu.

## Standalone + Supercharged — mandatory, not optional

Every command skill must work with **zero connectors**. It degrades gracefully, it never hard-fails because a connector isn't wired up. Structure the `## Inputs` section (or an early step) as two paths:

- **Without connected sources** — the user pastes text, uploads a file, or describes the input in the chat. This is the floor every skill must clear.
- **With `~~category` connected** — if the matching connector category is live, the skill can fetch directly instead of asking the user to hand it over manually. This is a strict improvement on the floor, never a substitute for it — a user without that connector configured must still be able to complete the task.

**Worked mini-example** — a "summarize meeting notes" command skill:

```markdown
## Inputs

Meeting notes to summarize.

**Without connected sources:** ask the user to paste the notes into the
chat, or upload a text/doc file. Work only from what's given — never
claim to have fetched something that wasn't provided.

**With ~~document store connected:** if a document-store connector is
active, offer to pull the notes directly (by file name, link, or a
quick search) instead of asking for a paste. Still accept a pasted or
uploaded file if the user doesn't have one queued up in the connected
source — the connected path is additive, not required.
```

Every command skill needs this shape somewhere in its body, even if the "with connector" path is currently a stub because the connector isn't wired up yet (see the CONNECTORS banner below).

## Cowork output hygiene

The skill runs in a VM / plugin-cache directory, not the user's visible file system — so file handling has hard rules, verbatim:

- Outputs go to the user's **working folder**. Never write into the plugin's own install directory or an arbitrary temp path.
- **No relative paths.** Resolve and use a real path rooted in the working folder.
- **No `open` / `xdg-open`.** The skill cannot pop a file open on the user's machine from inside the VM — don't attempt it, and don't write instructions implying it happened.
- **Tell the user the path.** After writing output, say exactly where it landed so the user can find and open it themselves.

For any skill where getting this wrong is costly — it writes many files, could overwrite existing work, or the working folder is otherwise load-bearing for the rest of the session — open the skill body with an explicit guard. Shown literally, the block reads:

```markdown
## MANDATORY FIRST STEP

Before doing anything else, confirm the user has a working folder open
in this Cowork session. If no working folder is selected, stop and ask
them to select one before continuing — do not generate, write, or
describe any output until a working folder is confirmed. Every file
this skill produces goes into that folder.
```

This guard is optional per skill, not a required section in every template — add it when the skill's output is sensitive or destructive enough to warrant halting up front; skip it for skills that only read or advise.

## The CONNECTORS.md banner

Every skill that touches an external tool — reads from a connector, writes through one, or references a `~~category` placeholder — emits this line, verbatim, near the top of its body (after `## Trigger`, before the skill gets into its own process):

```markdown
> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).
```

The relative path assumes the standard plugin layout, `skills/<skill-name>/SKILL.md` — two levels up from there lands at the plugin root, where `CONNECTORS.md` lives. If a skill is nested deeper, adjust the `../` count accordingly; don't copy the literal path blind.

This banner is written for Claude operating the skill, not for the Cowork end user reading the chat — it's a lookup pointer for resolving an unfamiliar `~~category` token or an empty-`url:""` stub, not conversational output. Which brings up the last rule.

## Nontechnical voice — what the user sees vs. what the skill body says

The skill body — frontmatter, `## Trigger`, the CONNECTORS banner, file paths, `~~category` tokens — is internal authoring material. It's written for you and for Claude reading its own instructions. None of it is meant to appear verbatim in what Claude actually says to the Cowork user during a conversation.

When the skill talks to the user, translate:

- No file paths or directory structure — say "I've saved this to your working folder as `summary.md`," not the resolved absolute path syntax used internally.
- No schema or frontmatter language — a user never hears "argument-hint" or "user-invocable."
- No raw `~~category` tokens — `~~document store` is an internal placeholder; the user hears "your connected document storage" or the actual connected product name, never the `~~` syntax itself.
- No mention of CONNECTORS.md, `.mcp.json`, or plugin-internal file names — if a connector's missing, the user hears "I don't see a connected [category] — you can paste the file instead," not a pointer to a file they can't open.

If a piece of skill-body prose would look strange read aloud to someone who has never seen a SKILL.md file, it's authoring material, not user copy — keep it out of the message the skill actually sends.
