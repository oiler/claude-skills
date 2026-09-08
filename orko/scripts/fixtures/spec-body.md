## Problem and intended outcome

Three call sites add two numbers inline, so their results drift apart whenever one is edited. The product must expose a single addition helper that every caller shares.

## Users and scenarios

A developer imports the helper and calls it with two numbers. A reviewer runs the test suite and sees the addition behavior covered by a named test.

## Evidence and classification

Verified: three call sites compute sums inline, checked 2026-09-08. Product decision: one helper replaces all three. Assumption: callers pass numbers rather than strings. Open question: none.

## Scope

Addition of two numeric arguments, returning their arithmetic sum.

## Non-goals

Subtraction, multiplication, arbitrary-precision arithmetic, and a command-line entry point.

## Requirements

### R1 — Return the sum

Given two numeric arguments, the helper must return their arithmetic sum. Given a non-numeric argument, it must raise a type error instead of returning a value.

## Failure and recovery behavior

A non-numeric argument raises a type error that names the offending argument. The caller recovers by converting the value and calling again. The helper writes no state, so there is nothing to roll back.

## Data, privacy, security, and accessibility

The helper stores nothing, logs nothing, and reads no user data. It runs in process under the caller's permissions and produces no user-visible output of its own.

## Compatibility and migration

A new helper with no stored data and no changed interfaces. Rollback is deleting the module and restoring the inline sums.

## Acceptance criteria

- Given the arguments 2 and 3, when the helper is called, then it returns 5.
- Given a string argument, when the helper is called, then it raises a type error and returns no value.

## Measures

Success: all three inline sums are replaced within one release. Guardrail: the test suite stays green.

## Dependencies, risks, and open questions

No external dependencies. oiler owns the acceptance decision.

## Amendments

None recorded.
