### Finding Verdicts
- **ASCII folding deletes separators (Paris–London -> parislondon)** — ADDRESSED. `textkit/slug.py:7` drops only combining marks; `tests/test_slug.py` pins `paris-london` and `tokyo-osaka`.

### New Breakage in the Fix Diff
1. **Important, `textkit/slug.py:7`.** Likelihood: moderate. Impact: wrong slugs. NFKD now runs before the lowercase step, so `ﬁle` (U+FB01) becomes `file` but `Ⅻ` (U+216B) becomes `xii`, splitting the documented one-to-one mapping the plan's Global Constraints state. Suggested fix: lowercase first.

### Out-of-Scope Observations
None.

### Verdict
**Fix round:** Findings remain open — the Important item above.
