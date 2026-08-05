---
name: meeting-notes
description: Turns raw meeting notes into a structured summary with decisions, action items, and owners. Use when the user says "summarize my meeting notes", "write up this meeting", "what did we decide", "pull the action items out of this", "turn my notes into a recap", or hands over a transcript, a set of bullet points, or a doc from a call and wants it cleaned up into something they can share.
argument-hint: [the notes file, or a short description of the meeting]
---

# /meeting-notes

## Trigger

When someone has messy notes from a meeting — bullets, a transcript, half-sentences typed while listening — and wants a clean recap they can send to the people who were not in the room.

## Inputs

- `$1` — the notes themselves: a file in the working folder, pasted text, or just the name of the meeting if the notes are already somewhere in this conversation.
- The meeting date, if it is not already in the notes. Ask once; do not guess.
- Who was in the meeting, if the notes do not name them. Owners on action items are the point of the summary, so it is worth one question.

## Steps

1. Read the notes end to end before writing anything. A recap written from the first third of a transcript reliably misses the decision.
2. Separate what was **decided** from what was **discussed**. Discussion that ended without a decision goes under open questions, not under decisions.
3. Pull out every action item. Each one needs an owner and, where the notes support it, a date. If the notes never say who owns something, write `owner unconfirmed` rather than assigning it to whoever spoke last.
4. Note anything raised and deliberately deferred — those are the items that quietly disappear between meetings.
5. Draft the summary in the shape under **Output Format**.
6. Save the summary into the user's working folder as `meeting-summary-<YYYY-MM-DD>.md`, using the meeting date. Then tell the user the file name and where it landed so they can find it themselves.
7. Show the decisions and action items in the reply as well. A summary the user has to go find is a summary they will not read.

## Without connected sources

This skill needs nothing connected. Ask the user to paste the notes into the chat or drop the file into their working folder, and work only from what they actually hand over.

Never invent attendees, decisions, or dates to fill a gap. If the notes are too thin to identify a decision, say so plainly and summarize what was discussed instead — a short honest recap is more useful than a padded one.

## With connected sources

If the user has a document or file-storage tool connected in Cowork, offer to pull the notes directly by name instead of asking for a paste. This is an addition to the path above, never a replacement for it: someone with nothing connected must still be able to finish the job by pasting.

If the user points at notes in a connected tool and that tool cannot be reached this session, stop and tell them — do not quietly fall back to whatever text happens to be in the chat.

## Output Format

A single markdown file, in this order:

- **Meeting** — name, date, attendees.
- **Decisions** — one line each, stated as a decision. No hedging, no attribution unless the notes make attribution matter.
- **Action items** — a table with three columns: what, who owns it, by when.
- **Open questions** — things raised without resolution, each with whatever context a reader needs to pick it up.
- **Notes** — anything worth keeping that does not fit the sections above. Keep this short; if it is long, the summary is not doing its job.

Two runs over the same notes should produce the same sections in the same order.

## After

- Offer: rewrite the summary as a short message the user can send to the team.
- Offer: pull only the action items into a checklist.
- Offer: summarize a second set of notes and compare what changed between the two meetings.
