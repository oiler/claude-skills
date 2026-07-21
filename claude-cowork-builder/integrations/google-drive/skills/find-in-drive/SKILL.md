---
name: find-in-drive
description: Searches ~~file storage (Google Drive) for files matching a name, keyword, or topic and hands matches off for reading. Use when the user says "find that file in Drive", "search my Google Drive for…", "look up the doc about…", "do I have a file called…", or asks to locate, find, or search for a file, document, spreadsheet, or presentation.
argument-hint: [search terms]
---

# /find-in-drive

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

## Trigger
When the user asks to find, search for, or locate a file, document,
spreadsheet, or presentation by name, keyword, or topic.

## Inputs
- `$1` — the search terms (a file name, keyword, or topic to look for).

## Steps
1. Take `$1` as the search terms.
2. Check whether `~~file storage` is connected (see CONNECTORS.md).
3. If connected, search it for files matching `$1`; if not, follow
   **Without connected sources** below.
4. Present the matches to the user — file name and file type are enough;
   don't surface raw IDs or paths.
5. If the user picks a match (or there's exactly one strong match), hand
   it off to `read-drive-file` to open and interpret — don't
   re-implement file reading here.
6. If nothing matches, say so and offer the standalone fallback.

## Without connected sources
If `~~file storage` is not connected, there's nothing to search — tell
the user you don't have a connected file storage source, and ask them to
upload the file directly or paste its contents instead. Proceed from
whatever they provide.

## With ~~file storage connected
Search the connected source for files matching `$1` by name and, where
the connector supports it, content. Return the closest matches rather
than an exhaustive list — a handful of well-ranked results beats a long
unranked one. Delegate opening a chosen file to `read-drive-file`;
this skill's job ends at finding and listing candidates.

## Output Format
If the user asks for a written record of the search (e.g. a shortlist to
review later), write it to the user's working folder and tell them the
exact path to open it. Never use a relative path, and never try to open
or launch the file for them (no `open`/`xdg-open`) — for a normal
in-chat search, just present the matches directly in the reply; a file
isn't required for every search.

## After
- Offer: open one of the matched files now (via `read-drive-file`).
- Offer: refine the search with different terms.
- Offer: search a different connected source, if more than one is
  configured.
