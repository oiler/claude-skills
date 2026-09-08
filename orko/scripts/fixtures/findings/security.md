### FINDINGS — Seat: security
- Verdict: one upload path accepts unbounded input
- Confidence & gaps: did not exercise the running service

#### F1 — Upload path is unbounded
- Severity: high
- Evidence: code/app/upload.py line 31, no size or type check before write
- Requirement: SPEC-001 R5
- Impact: a large or hostile file fills the disk
- Recommendation: cap the request body and reject unknown content types
