# SDD ledger — plan: docs/plan.md

Task 3: skipped — evergreen conflict — CLAUDE.md:3 — plan requires adding `requests` and `beautifulsoup4` to pyproject.toml; CLAUDE.md says standard library only and never add third-party deps, including to pyproject.toml
Task 4: skipped — depends on Task 3
Task 3: skip decision — (a) rewrite Task 3 on stdlib `urllib.request` + `html.parser` and run Tasks 3-4; (b) amend CLAUDE.md to allow these deps and run as written; (c) drop URL titles from scope. Recommend (a).
Task 1: dispatch implementer-scoped sonnet/medium — plan text has complete code and tests
Task 1: dispatch reviewer opus/medium — pure string transform, not security-sensitive
Task 1: minor (deferred): slugify drops non-ASCII letters ("Café" -> "caf"); plan-mandated code; NFKD normalization would fix it
Task 1: complete (commits 42737fc..84e4e37, review clean)
Task 2: dispatch implementer-gap opus/low — prose task with small open points, each ruled; stdin filter
Task 2: dispatch reviewer-security opus/high — CLI reads stdin and argv; gets web-security line
Task 2: minor (deferred): invalid UTF-8 on stdin crashes with an uncaught UnicodeDecodeError traceback
Task 2: complete (commits 84e4e37..8ffd986, review clean)
Task final: dispatch final-reviewer opus/high — ordinary whole-branch review; Task 2 got web-security line
Ruling: final Issue 2 — change plan-mandated slugify to NFKD-normalize and ASCII-fold before the regex ("Café" -> "cafe") — the plan's own tests still pass and silently dropping letters is not what a slug user expects; stdlib only — cost if wrong: one-line revert in textkit/slug.py and one test
Ruling: final Issue 1 — decode stdin with errors="replace" so invalid bytes become separators and good lines still produce slugs, rather than exiting with an error — a line filter should not lose all output on one bad byte — cost if wrong: swap to a clean error exit; small change in cli.py and its test
Task final: dispatch final-fixer opus/medium — single fix wave: stdin decode, NFKD slugify, __main__.py, .gitignore
Task final: dispatch re-reviewer-security opus/high — scoped re-review of fix wave touching stdin decoding
Ruling (supersedes "change plan-mandated slugify to NFKD-normalize"): final Issue 2 — after NFKD, drop only combining marks and let the regex turn the rest into separators — the ASCII fold deleted separators (Paris–London -> parislondon) — cost if wrong: one helper in textkit/slug.py
Task final: dispatch final-refixer opus/high — Important regression from the fix wave: ASCII folding deletes separators
Task final: dispatch re-reviewer-security opus/high — refix re-review
