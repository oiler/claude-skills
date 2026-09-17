---
id: PLAN-NNN
title: "[Delivery plan]"
status: draft
product_version: "[MAJOR.MINOR]"
implements:
  - SPEC-NNN
owner: "[engineering owner]"
---

# PLAN-NNN — [Delivery plan]

## Summary

<!-- Explain the delivery approach and why it fits the accepted requirements. -->

## Preconditions and dependencies

<!-- Link decisions, research, interfaces, teams, environments, or unresolved questions. -->

## Requirement mapping

| Requirement | Implementation area | Verification evidence | Performed by |
| --- | --- | --- | --- |
| SPEC-NNN R1 | [Module or interface] | [Test or acceptance case] | [agent/owner] |

<!-- Performed by is `agent` when a test or script produces the evidence, `owner` when only a human observation can. Owner rows are never delegated to a subagent; the plan is blocked until the owner records the result. -->

## Delivery decisions

<!-- Choices made while planning that are neither product requirements nor ADR-worthy. Route first: a choice that changes externally observable behavior is a specification amendment; a choice with long-lived architectural consequence is an ADR. Everything else is recorded here and inherits this plan's status. -->

| Decision | Rationale | Approved by |
| --- | --- | --- |
| [Choice] | [Why] | [Approver] |

## Delivery sequence

<!-- Describe independently reviewable increments, migrations, feature flags, and rollout order. Any commit or pull-request command written into a task brief carries the session's attribution trailers verbatim. -->

## Testing and acceptance

<!-- Cover unit, integration, end-to-end, manual, performance, security, accessibility, and rollback checks as applicable. -->

### Mutation verification

<!-- For each guard that folds two or more conditions into one call, list one mutation per condition, each tied to exactly one test that must go red. A mutation that cannot be tied to one test means the test design is wrong; fix it before code is written. A surviving mutation is not equivalent until the covered input space is enumerated. -->

| Guard | Mutation | Test that must fail |
| --- | --- | --- |
| [Guard] | [Single condition removed or inverted] | [Test name] |

## Risks and mitigations

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| [Risk] | [Impact] | [Mitigation] | [Owner] |

## Rollout and rollback

<!-- Define observability, stop conditions, rollback method, and data recovery. -->

## Open questions

<!-- Plans must not silently decide unresolved product behavior. -->
