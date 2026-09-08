# Agent Instructions — Product Documentation

## Repository purpose

This repository is the authoritative record of product intent: objectives, evidence, scope, product decisions, behavioral specifications, delivery plans, reviews, acceptance, and releases. It does not contain production implementation.

## Authority order

When sources conflict, use this order and report the conflict:

1. Released records for historical claims about a release
2. Accepted specifications for required product behavior
3. Accepted product decision records
4. The active version scope
5. `OBJECTIVE.md`
6. Roadmap, research, plans, and status documents

Never silently reconcile conflicting authoritative documents.

## Required behavior

- Read `OBJECTIVE.md`, `STATUS.md`, the active version README, relevant accepted specifications, and applicable product-design guidance before proposing implementation work.
- Preserve stable artifact IDs in filenames, headings, links, commits, and reviews.
- Separate verified facts, decisions, hypotheses, assumptions, and open questions.
- Treat acceptance criteria as externally observable behavior, not implementation instructions.
- Keep product experience, interaction, and accessibility guidance in `design/`; keep software architecture and the front-end style guide (`DESIGN.md`) in the code repository.
- Add links to evidence and record when time-sensitive evidence was checked.
- Follow `policies/CHANGE-CONTROL.md`, `policies/VERSIONING.md`, `policies/TRACEABILITY.md`, and `policies/RELEASE.md`.
- Report unresolved ambiguity instead of inventing product requirements.

## Change boundaries

- Draft artifacts may be edited directly.
- Accepted specifications may only be amended, returned to draft before implementation, or superseded.
- Accepted decisions are superseded, not rewritten to conceal the original decision.
- Released manifests and completed acceptance records are historical records and must not be rewritten. Correct them with a linked follow-up record.
- Do not declare acceptance, approval, or release without evidence of human authorization.
- Do not edit the code repository unless the task explicitly includes implementation work.

## Document status

Use one of: `proposed`, `draft`, `in_review`, `accepted`, `superseded`, `withdrawn`. Decision records start as `proposed`; other artifacts start as `draft`. Release records may additionally use `planned` and `released`. Version dossiers use a workstream lifecycle instead: `proposed`, `active`, `closed`.

## Before finishing

- Check links, IDs, status fields, version references, and unresolved placeholders.
- Summarize changed requirements, new decisions, waivers, and open questions.
- Identify which code-side documents or manifests must be updated.
