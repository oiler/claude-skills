## Lens: verification

For each task, check how anyone would know it worked:

- A runnable check exists and would fail without the change. A check that passes either way is a finding.
- Logic is built red/green: the failing test is written and run before the implementation.
- Tests are sized like the repo's neighbors: one focused test per stated behavior, no scratch checks promoted to permanent tests.
- Every load-bearing fact in the spec has a step somewhere that verifies it in the built result.
- Expected output shown for commands is plausible for that command.
