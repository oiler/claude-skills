---
name: read-drive-file
description: Explains how to open, read, and interpret a file from ~~file storage (Google Drive) once it has been located — export formats for Docs/Sheets/Slides, how to handle PDFs/images/CSVs/plain text, and how to hand the content off for summarizing or answering questions. Use when a command skill needs to read a specific Drive file, when the user references "that doc", "the spreadsheet", "the file in my Drive", asks to open/read/summarize/extract from a Google Drive file, or when find-in-drive has matched a file and needs it interpreted.
user-invocable: false
---

# read-drive-file

Background knowledge Claude loads on demand for reading and interpreting a
file from `~~file storage`. Written as instructions for Claude, not the
user.

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

## Scope

Covers reading the *content* of a single, already-identified file — not
searching for one (that's `find-in-drive`). Any skill that ends up holding
a file reference (a name, an ID, a link, or a search result) delegates the
"now read it" step to this skill rather than re-implementing format
handling inline.

## Rules

**Without connected sources.** If `~~file storage` is not connected, or
the specific file isn't reachable through it, ask the user to upload the
file directly into the chat or paste its contents. Work only from what's
given — never claim to have opened or read a file that wasn't actually
provided. This is the floor: it must produce a usable result with zero
connectors configured.

**With `~~file storage` connected.** Fetch the file through the connected
source using whatever reference is in hand (name, ID, or link). Match by
format:

- **Google Docs** — read as exported plain text/markdown; preserve
  headings and lists where the export provides structure, but don't
  invent structure that isn't there.
- **Google Sheets** — read as exported CSV or a structured table; keep
  the original row/column shape rather than flattening it into prose
  until asked to summarize.
- **Google Slides** — read as exported text per slide; keep slide
  boundaries visible so downstream summarizing can reference "slide 3"
  correctly.
- **PDF, plain text, CSV, images** — read natively; for images, describe
  or extract only what's visibly present, don't guess at content that
  isn't legible.

If a file's format can't be determined or read cleanly, say so plainly
and fall back to the standalone path — ask the user to upload it directly
— rather than guessing at its contents.

**Handing off content.** Once read, pass the content to whatever asked
for it (a summarizer, a search, a direct answer) without restating the
whole file back to the user unless they asked to see it. Tell the user,
in plain language, which file was read (by name, not by ID or path) —
never surface a raw Drive file ID or internal path in the reply.
