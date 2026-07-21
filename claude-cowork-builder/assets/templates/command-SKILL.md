---
name: COMMAND_NAME
description: Third-person, trigger-rich. Use when the user says "…" or "…".
argument-hint: [what $1 is]
---

# /COMMAND_NAME

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

## Trigger
When the user asks to … (plain language).

## Inputs
- `$1` — …

## Steps
1. …

## Without connected sources
If ~~category is not connected, ask the user to paste/upload/describe the input, then proceed.

## With ~~category connected
Use the connected tool to …

## Output Format
Write the deliverable to the user's working folder and tell them the path to open. Never use relative paths or open/xdg-open.

## After
- Offer: …
- Offer: …
