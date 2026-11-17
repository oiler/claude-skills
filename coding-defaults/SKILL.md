---
name: coding-defaults
description: oiler's default rules for writing code and tests in any language. Use whenever writing, editing, refactoring, or testing code, including bug fixes, new files, and adding or running tests. A project's own rules (its CLAUDE.md, AGENTS.md, style guide, or linter config) win over this skill wherever they conflict.
---

# Coding defaults

Defaults for any code change. A project's own rules (its CLAUDE.md, AGENTS.md, style guide, or linter config) override these wherever they conflict.

## Code

- Edit existing files rather than creating new ones.
- Prefer a surgical edit over rewriting a whole file when the end result is the same.
- Match the codebase's existing style rather than imposing a new one. If it has a style guide or linter config, defer to it; if it has neither, ask before introducing conventions of your own.
- Comment on *why*, not *what*. Skip the comment when the name already explains it.
- No backwards-compat shims, dead-code "removed" comments, or unused-variable hacks.
- Three similar lines beat a premature abstraction. Don't add configurability or extension points the task doesn't need.
- Don't add error handling, fallbacks, or validation for cases that can't happen; trust internal contracts and framework guarantees. Validate at system boundaries: user input, external APIs, files, the network.
- Avoid circular imports.

## Testing

**Every test goes red before it goes green.** Write the test, run it, and see it fail for the expected reason; then write the code or fix that makes it pass. A test that has never failed hasn't proven anything.

**Write tests where they pay off:**

- the observable proof that a milestone works: an end-to-end run with an artifact
- a regression test for every real bug, at the lowest level that reproduces it
- isolated tests on a high-risk boundary (parsing, validation, security, idempotency, money) when the change adds or alters behavior there, covering the failure modes the change can trigger
- property tests for round-trips (encode then decode returns the input), invariants, and idempotency, using a property library such as Hypothesis or fast-check
- differential tests for migrations: run the old and new code on the same inputs and compare

**Don't write** tests that restate code, check prose, or only ever run against fakes when the real thing is reachable. Scratch checks stay scratch; don't promote them into permanent test files.

**Failing checks:** if a check still fails after three rounds of fixes, stop and bring me in.

**Flaky tests:** don't skip them, retry until they pass, or add sleeps. Find the root cause; if you can't, delete the test and write down why.

**Existing code with no test** (before a refactor, for example): prove the new test can fail by temporarily breaking the code it covers, then restore the code.
