---
name: crm-sync
description: Helps with ~~CRM tasks.
argument-hint: [what to tidy up]
---

# /crm-sync

## Trigger

When someone wants their CRM records tidied up after a busy week.

## Inputs

- `$1` — what to tidy: a company name, a deal stage, or "everything from this week".

## Steps

1. Read the records for whatever `$1` names.
2. Flag records missing an owner, a stage, or a next step.
3. Flag duplicates — the same company entered twice under slightly different names.
4. Present the list of problems to the user and ask which ones to fix.
5. Apply the fixes the user approves.

## With your CRM connected

This skill requires your CRM connector. Read the records through the connector, apply the approved fixes, and report back how many records changed.

If the connector is not configured, tell the user the skill cannot run and point them at connecting their CRM first.

## Output Format

A short list in the chat: records with problems, grouped by the kind of problem, most common kind first. If the user asks for a written copy, save it to the working folder and tell them the file name.

## After

- Offer: fix the remaining flagged records.
- Offer: run the same check on a different set of records.
