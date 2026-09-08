## Summary

Add one addition helper in `src/calc.py` and point the three inline call sites at it, because the accepted requirement asks for a single shared result.

## Preconditions and dependencies

None. The module is new and depends only on the standard library.

## Requirement mapping

| Requirement | Implementation area | Verification evidence | Performed by |
| --- | --- | --- | --- |
| SPEC-001 R1 | src/calc.py | test_add | agent |

<!-- Performed by is `agent` when a test or script produces the evidence, `owner` when only a human observation can. Owner rows are never delegated to a subagent; the plan is blocked until the owner records the result. -->

## Delivery decisions

The helper takes positional arguments only, which keeps the three call sites unchanged apart from the import.

| Decision | Rationale | Approved by |
| --- | --- | --- |

## Delivery sequence

One increment: add the helper with its test, then replace the three inline sums in a follow-up commit.

## Testing and acceptance

Unit tests cover the sum and the type error. No integration, performance, or accessibility work applies.

### Mutation verification

The type guard folds one condition, so one mutation is enough: dropping the numeric check must turn `test_add_rejects_strings` red.

| Guard | Mutation | Test that must fail |
| --- | --- | --- |

## Risks and mitigations

| Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- |

## Rollout and rollback

The helper ships with the next release. Rollback is deleting the module and restoring the inline sums.

## Open questions

None.
