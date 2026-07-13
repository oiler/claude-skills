# Changelog — cloud-run-functions

All notable changes to the `cloud-run-functions` skill.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is [semver](https://semver.org/), tagged per-skill as `cloud-run-functions-vX.Y.Z`.

## [0.1.0] — 2026-07-13

Initial release.

### Added

- **Stage 0 fit gate** — five ordered checks (duration, post-response work, hardware/system deps, traffic shape, payload size) run *before* any code is written. A workload that fails a check is named, sourced, and routed to the service that fits (Cloud Run service, job, worker pool, Workflows, Cloud Tasks, Batch) rather than being built and caveated.
- **Six-stage build pipeline** — handler, local uv loop, one-time project setup, deploy, live verify, teardown. HTTP is the default path.
- `references/fit-and-limits.md` — every hard limit with a source URL, the cost model and its four cliffs, the Cloud SQL connection math, and the function/service/job/worker-pool decision table. Google's own doc conflicts are flagged as conflicts rather than resolved by guessing.
- `references/event-triggers.md` — Pub/Sub, Cloud Storage, Eventarc. Decorators, deploy flags, local CloudEvent testing, at-least-once idempotency, retry-default divergence between the Admin API and the Functions v2 API, and the infinite-retry guard.
- `references/workspace-and-ai-bridges.md` — Workspace Events API, Gmail push, Chat apps, Add-ons alternate runtimes, Apps Script handoff, AppSheet, domain-wide delegation, and Gemini/Vertex/MCP patterns.
- `references/troubleshooting.md` — failure map, ordered by frequency, including the three that only appear under sustained load.

### Notes

Limits verified against Google's live documentation on 2026-07-13. The source handoff doc marked most of its infrastructure claims as extrapolated-not-run; those were re-verified rather than inherited, which surfaced two corrections worth calling out:

- **Event-driven functions are capped at 540 seconds, not 60 minutes.** The gen2 timeout increase applies to HTTP triggers only. The 9-minute gen1 cap never lifted for Pub/Sub, Eventarc, or Cloud Storage triggers.
- **Eventarc events cap at 512 KB** — 64× smaller than the 32 MiB HTTP request limit. Events carry pointers, not payloads.

Both are load-bearing for the Workspace bridges, which deliver through Pub/Sub and are therefore event-driven.
