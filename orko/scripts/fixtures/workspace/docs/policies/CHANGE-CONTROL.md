# Change-Control Policy

## Living documents

Objectives, roadmaps, research, status reports, draft specifications, and draft plans may evolve. Material changes should explain what changed and why.

## Controlled documents

An accepted specification may only change by:

1. returning it to draft before implementation begins;
2. adding a dated amendment that preserves the original requirement; or
3. superseding it with a new specification.

Accepted product decisions are superseded by new decision records rather than silently rewritten.

## Readiness

Before marking a specification accepted, run `scripts/spec-check.sh SPEC-NNN` from the code repository. It reports empty sections, missing requirements or acceptance criteria, leftover placeholders, and plan-mapping gaps. It is advisory here and required at release.

## Historical records

Released manifests and completed acceptance records describe historical events. Do not rewrite them to match current understanding. Correct an error with a linked correction or follow-up record.

## Approval

Only a named human approver may mark an artifact accepted, waived, or released. An AI agent may prepare the change and record supplied approval, but may not infer approval.

## Enforcement

This scaffold uses review discipline rather than automation. Repository owners should use protected branches, protected release tags, and appropriate reviewers when their hosting platform supports them.
