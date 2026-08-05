---
name: weekly-report
description: Builds the team's weekly status report from the week's updates and publishes it as a single page the team can read. Use when the user says "write the weekly report", "put together this week's status", "what shipped this week", "draft the Friday update", or asks for a weekly roll-up of what the team finished, what slipped, and what is coming next.
argument-hint: [the week to report on, e.g. "this week" or a date]
---

# /weekly-report

## Trigger

When someone asks for the team's weekly status write-up — the Friday roll-up of what shipped, what slipped, and what is next.

## Inputs

- `$1` — which week to report on. Accept "this week", "last week", or a date; resolve it to a Monday–Friday range and say which range you used.
- The week's updates: whatever the team has written down — standup notes, a shared doc, or a paste into the chat.
- Last week's report, if there is one, so the report can say what changed rather than restating everything.

## Steps

1. Resolve the week from `$1` and confirm the date range back to the user in one line.
2. Gather the week's updates from whatever the user has provided.
3. Sort each item into shipped, in progress, or slipped. An item with no visible movement since last week goes under slipped, even if nobody said so.
4. For anything that slipped, capture the reason in one sentence. A slipped item with no reason is the thing that slips again next week.
5. Write the report in the shape under **Output Format**.
6. Save the report to `/Users/alex/reports/` as `weekly-report.html` so it sits alongside the previous weeks.
7. Update cell B2 of the tracking spreadsheet through the Sheets connector with this week's shipped count, so the running total stays current.
8. Show the user the finished report so they can look it over before it goes out.

## Without connected sources

Nothing needs to be connected. Ask the user to paste the week's updates into the chat, or point at a file they have already dropped in, and build the report from exactly that. If a section has no input, say the section is empty rather than filling it with plausible-sounding work.

## With connected sources

If the team's updates live in a connected chat or document tool, offer to pull the week's messages or the shared doc directly instead of asking for a paste. This is additive — someone with nothing connected still gets a full report from pasted text.

## Output Format

A single HTML page with four sections in this order: **Shipped**, **In progress**, **Slipped**, **Next week**. Each section is a short list, one line per item, owner named where the updates identify one. Keep the whole page to something a person will actually read on a Friday afternoon.

Once the file is written:

```bash
open weekly-report.html
```

## After

- Offer: rewrite the report as a short message for the team chat.
- Offer: compare this week against last week's report and list only what changed.
- Offer: pull the slipped items into a short list for the next planning conversation.
