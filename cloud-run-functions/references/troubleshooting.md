# Troubleshooting

Ordered roughly by how often each one happens.

## Deploy fails

| Symptom | Cause | Fix |
|---|---|---|
| `PERMISSION_DENIED` / "API not enabled" | One of the four APIs isn't on | `gcloud services enable run.googleapis.com cloudfunctions.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com` (+ `eventarc`, `pubsub` for event triggers) |
| Billing error | No billing account linked | Link one. **The free tier still requires billing enabled** — deploy fails outright without it |
| Build fails compiling a dependency | The package needs a system library, or has no wheel for the runtime | Check for a wheel matching the runtime version. If it needs `apt` packages, **buildpacks cannot help you** — write a Dockerfile, which means you're now a Cloud Run *service* |
| Trigger source not found | Topic/bucket doesn't exist yet | Create it before deploying — the trigger binds to an existing resource |
| Deploy quota exceeded in CI | Admin API write quota is **60 per 60 seconds and cannot be raised** | Serialize or throttle parallel deploys |

## It deployed, but calling it fails

| Symptom | Cause | Fix |
|---|---|---|
| `403` on curl | Function is IAM-gated (no `--allow-unauthenticated`) | `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <url>` — or decide, deliberately, to make it public |
| `Function 'X' not found` on describe/logs/delete | **Region mismatch** | Pass the same `--region` to every command. This reads like a failed deploy and isn't |
| `500`, logs show "no attribute" | `--entry-point` doesn't match the decorated Python function name | Align them. It's the *function* name, not the filename |
| `ModuleNotFoundError` in cloud, works locally | The dep is in your local venv but not in `requirements.txt` | Add it. **`requirements.txt` is the deploy manifest** — the buildpack never reads `pyproject.toml` or `uv.lock` |
| `504` after a long wait | Hit the request timeout | Check which ceiling applies: **60 min HTTP, 540s event-driven**. Note you are **billed for the full timeout window** |

## It works, then breaks under load

These are the nasty ones, because they don't reproduce in testing.

| Symptom | Cause | Fix |
|---|---|---|
| **Connection reset errors in invocations you didn't make** | Background work continuing after the response returned. Default billing **throttles CPU to ~zero** the moment you return, and the orphaned work interferes with the *next* request on that warm instance | Do the work before returning; or move it to a worker pool / job; or switch to instance-based billing. See `fit-and-limits.md` → CPU throttling |
| Gradual OOM under sustained traffic | Temp files. `/tmp` is **tmpfs — it eats your memory limit**, and files **persist across invocations on a warm instance** | Delete temp files explicitly. Or mount a GCS/NFS volume |
| Database "too many connections" | Cloud Run allows **100 connections to Cloud SQL per instance**, and you have up to max-instances of them | Cap `--max-instances`, size the pool to 1–2 per instance, consider Managed Connection Pooling |
| Cache "randomly" misses | Global-scope cache is **per-instance and never shared**. There is no cross-instance cache | Memorystore/Redis for anything that must be coherent |
| Corrupted shared state | Mutable global with concurrency > 1 | Lock it, or don't share it |
| Bill is much larger than expected | Usually concurrency-1 (often forced by fractional CPU) or a hung function billing its full timeout | See `fit-and-limits.md` → cost cliffs. Concurrency 1 vs 20 was a **6× difference** in Google's own example |
| Duplicate side effects (double charge, double email) | **At-least-once delivery.** Duplicates are part of the contract, not an anomaly | Idempotency keyed on the event ID. See `event-triggers.md` |
| An event retries for hours | Poison event, 24-hour retry window | Add an event-age guard that acks and drops old events |

## Empty or missing logs

- `print()` to stdout lands in Cloud Logging. If nothing appears at all, first confirm the **region** on `logs read` matches the deploy.
- For event functions: a successful deploy doesn't mean a live trigger — **binding can take several minutes**. A message published immediately after deploy may simply have had nothing listening.
- Check that the function was actually invoked (Cloud Run metrics) before debugging code that may never have run.

## Local behaves differently from cloud

| Cause | Fix |
|---|---|
| Python version drift | `uv venv --python 3.12` — pin local to the deployed runtime |
| Dep in venv but not in `requirements.txt` | The manifest is `requirements.txt`, full stop |
| Ambient credentials locally, none in cloud | The deployed function uses its **service account**. Grant it the roles it needs (`roles/cloudsql.client`, `roles/aiplatform.user`, …) |
| Something in your source dir didn't upload | `--source=.` respects `.gcloudignore` — check you didn't exclude something load-bearing |

## Suspect the platform, check these first

- **Port 25 (SMTP) is blocked.** Outbound mail will not work. Use an email API.
- **`sys.exit()` in a handler** kills the instance. Never do it.
- **A handler that never returns** runs to timeout and bills the entire window.
- **Fractional CPU (<1 vCPU)** silently forces concurrency 1, request-based billing, and the gen1 execution environment.
