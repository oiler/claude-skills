# Agent Instructions — Software

## Repository purpose

This repository is the authoritative implementation, test, build, and operational record. Product intent is authoritative in the companion docs repository.

Docs repository: `[organization/project-docs]`

## Required context

Before changing behavior, identify the active product version and read its accepted specifications, decisions, delivery plan, and acceptance criteria. Use the exact documentation baseline referenced by the work item when available.

If implementation needs behavior not defined by an accepted specification, stop and raise a product question. Do not convert an engineering assumption into product policy.

## Required behavior

- Cite relevant `SPEC-NNN`, `FIX-NNN`, `PLAN-NNN`, and `ADR-NNN` IDs in change descriptions.
- Map externally observable changes to tests or acceptance evidence.
- Preserve compatibility, migration, security, privacy, accessibility, and rollback requirements.
- Update `ARCHITECTURE.md` when the current architecture changes materially, and `DESIGN.md` when visual tokens or component styling change.
- Add an ADR for consequential technical choices with meaningful alternatives or long-lived consequences.
- Keep generated output separate from source and state whether it is committed.
- Never claim approval, acceptance, or release without evidence of human authorization.

## Change boundaries

- Do not change accepted product requirements from this repository.
- Do not edit the docs repository unless the task explicitly includes product documentation work.
- Do not commit secrets, credentials, personal data, local configuration, or unreviewed generated artifacts.
- Do not weaken tests merely to make a change pass.
- Avoid destructive data migrations without an explicit recovery and approval path.

## Document status

Use one of: `proposed`, `draft`, `in_review`, `accepted`, `superseded`, `withdrawn`. ADRs start as `proposed`; other documents start as `draft`.

## Validation

Project-specific commands belong in `CONTRIBUTING.md`. Until defined, report that validation is unspecified rather than inventing a successful check.

Before finishing, summarize implementation changes, validation performed, residual risks, and docs-side records that require updates.
