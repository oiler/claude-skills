---
name: cloud-run-functions
description: Build, deploy, debug, and cost-tune Google Cloud Run functions (formerly Cloud Functions gen2) in Python — AND judge whether a workload belongs in a function at all. Use whenever the user mentions Cloud Run functions, Cloud Functions, "gcloud functions deploy", functions-framework, an HTTP function, a Pub/Sub-triggered or Cloud Storage-triggered function, Eventarc, a serverless function on GCP, an unexpected Cloud Run bill, or wants to put some job "in a cloud function". Also use when the user proposes a Cloud Run function for something and you should sanity-check the fit — long-running work, background threads, GPU/ML inference, WebSockets, large payloads, system packages like ffmpeg, and high-QPS low-concurrency traffic are common misfits that belong in a Cloud Run service, job, or worker pool instead. Covers the fit gate, the local uv loop, deploy, verify, teardown, event triggers, idempotency, cost, and Google Workspace / Gemini bridges. NOT for: Cloud Run *services* built from a Dockerfile as the primary task, GKE, or App Engine.
allowed-tools: Bash(gcloud *) Bash(uv *) Bash(curl *) Bash(functions-framework *)
metadata:
  author: oiler
  version: 0.1.0
---

# Cloud Run functions (Python)

Two jobs, in this order: **decide whether this belongs in a function**, then **build it well**.

The second job is easy and well-documented. The first is where projects actually go wrong — someone reaches for a function because it's the cheapest thing to spin up, then discovers nine months later that the 540-second event timeout, the throttled-CPU-after-response rule, or the concurrency-1 billing shape is structural and unfixable without a rewrite. Catching that in the first five minutes is the highest-value thing this skill does.

## The one fact that reframes everything

**Cloud Run functions *are* Cloud Run services.** Google says so directly: source deploys and functions "operate as Cloud Run services and are billed accordingly." A function is a *packaging convention* — buildpacks + Functions Framework + one entry point — not a separate runtime.

This has a liberating consequence and a trapping one:

- **Liberating**: nearly every Cloud Run service capability is available (volume mounts, streaming, WebSockets, VPC egress, 32 GiB), and "graduating" a function to a service is a repackaging, not a migration.
- **Trapping**: the handful of places where the *function* surface is more restrictive than the service underneath are invisible until they bite. Those are listed in the fit gate below.

## Stage 0 — The fit gate (do this before writing any code)

When the user proposes putting a workload in a Cloud Run function, run these five checks first. They take a minute and they are ordered by how expensive the mistake is to unwind.

| # | Ask | Disqualifier | Where it belongs instead |
|---|---|---|---|
| 1 | **How long can one invocation run?** | >9 min on an **event trigger** (Pub/Sub, Eventarc, GCS) — hard cap **540s**. >60 min on **HTTP**. | Cloud Run **job** (up to 7 days), or a **worker pool** with a Pub/Sub *pull* subscription (no request timeout at all) |
| 2 | **Does any work continue after the response returns?** | Background threads, `asyncio.create_task`, fire-and-forget cleanup. Default billing **throttles CPU to ~zero the instant you return** — this is the single most common Cloud Run functions bug, and it surfaces as connection-reset errors in the *next* invocation, not this one. | Instance-based billing (always-on CPU), a **worker pool**, or a **job** |
| 3 | **What hardware / system deps does it need?** | A **GPU** (documented for services/jobs/worker pools — **not** for functions). Any **apt/system package** (`ffmpeg`, `libvips`, `poppler`) — buildpacks have no mechanism for these. >16 GiB / >4 vCPU via the functions API surface. | Cloud Run **service** with a Dockerfile. The moment you need a Dockerfile you *are* a service — that's the cleanest dividing line there is. |
| 4 | **What's the traffic shape?** | Steady high QPS at concurrency 1. Request-based billing charges $0.40/M requests *plus* a 25% CPU premium over instance-based. Google's own example: 10M requests at concurrency 20 = **$13.69/mo**; identical work at concurrency 1 = **$81.72/mo**. A 6× swing from one setting. | Cloud Run **service** with instance-based billing, or raise concurrency |
| 5 | **How big is the payload?** | **512 KB** on the Eventarc/event path — 64× smaller than the 32 MiB HTTP limit. | Pass a **GCS object pointer**, not the object |

**If all five pass, proceed to Stage 1.** If any fails, say so plainly, name the specific limit and the service that fits instead, and ask before building. Don't build the function and bury the caveat in a comment — the user asked for a function because they hadn't hit the limit yet, and the whole point of the gate is to surface it while a redesign is still cheap.

Two more disqualifiers that are less about limits and more about shape:
- **Long-lived streams** (WebSockets, SSE, gRPC) technically work — a WebSocket is just an HTTP request — but they're bound by the request timeout, so a 9-minute event-driven cap makes this a services-only pattern in practice.
- **Local persistent state.** There's no persistent disk. `/tmp` is **tmpfs — it consumes your memory limit**, and files can survive between invocations on a warm instance, so a leaked temp file becomes a slow OOM. Use GCS/NFS volume mounts (yes, functions can mount them) or Memorystore.

Full numbers, sources, and the conflicts in Google's own docs: **`references/fit-and-limits.md`**. Read it whenever the gate is close to the line, or when the user pushes back on a disqualification.

## Stage 1–6 — The build pipeline

Once the gate passes, every function follows the same six stages. Stages 1–2 are the tight local loop; stage 3 is once per project; 4–6 repeat per deploy.

### 1. Write the handler

`main.py` at the source root, one decorated entry point:

```python
import functions_framework


@functions_framework.http
def hello(request):
    name = request.args.get("name", "World")
    return f"Hello, {name}!\n"
```

Returning a `str` yields a 200 with that body; return `(body, status)` to set the code, or a Flask `Response` for full control.

`requirements.txt` — **this is the deploy manifest.** The buildpack reads `requirements.txt`; it does *not* read `pyproject.toml` or `uv.lock`. `uv` is a local-only accelerator here. Keep `requirements.txt` as the single source of truth for a simple function; if the project graduates to a `pyproject.toml`, regenerate with `uv export --no-hashes --format requirements-txt > requirements.txt` before each deploy.

`.gcloudignore` — `--source=.` respects it. Keep `.venv/`, `__pycache__/`, and docs out of the upload.

Cache expensive clients (DB connections, API clients) at **module scope** — globals persist across invocations on a warm instance and this is Google's recommended cold-start mitigation. But that cache is *per-instance and never shared*, and with concurrency >1 a mutable global is a race. Anything that must be coherent across instances goes in Memorystore.

### 2. Local loop (verify before you ever deploy)

```bash
uv venv --python 3.12          # pin to the deployed runtime — avoids "works locally, breaks in cloud"
uv pip install -r requirements.txt
uv run functions-framework --target=hello --debug
curl 'localhost:8080/?name=Justen'
```

Event-driven functions run locally too — functions-framework serves them over HTTP and you POST a CloudEvent envelope at `localhost:8080`. See `references/event-triggers.md`.

### 3. Project setup (once)

```bash
gcloud projects create <PROJECT_ID> --name="<NAME>"
gcloud config set project <PROJECT_ID>
gcloud billing projects link <PROJECT_ID> --billing-account=<ACCOUNT_ID>
gcloud services enable run.googleapis.com cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Four APIs, and why each: `cloudfunctions` is the control plane, `run` is what gen2 functions actually run on, `cloudbuild` turns source into a container, `artifactregistry` stores the image. Event triggers add `eventarc.googleapis.com` and usually `pubsub.googleapis.com`.

**Billing must be linked even inside the free tier** — deploy fails outright without it, though hello-world traffic costs nothing.

### 4. Deploy

```bash
gcloud functions deploy <NAME> --gen2 --runtime=python312 --region=<REGION> \
  --source=. --entry-point=<ENTRY_POINT> --trigger-http [--allow-unauthenticated]
```

- `--gen2` always. gen1 is legacy and has concurrency hard-pinned to 1.
- `--entry-point` is the **Python function name**, not the filename.
- `--allow-unauthenticated` makes the URL **publicly reachable by anyone who has it**. That's an authorization decision, not a convenience flag — treat it as one, and route exposure/input-handling questions to the **web-security** skill. The authenticated alternative: omit the flag and call with `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <url>`.

### 5. Verify live

```bash
gcloud functions describe <NAME> --gen2 --region=<REGION> --format='value(serviceConfig.uri)'
gcloud functions logs read <NAME> --gen2 --region=<REGION> --limit=20
```

Exercise the real trigger and read the logs. A deploy that succeeded is not a function that works.

**Region must match across every command** — `deploy`, `describe`, `logs read`, `delete`. A mismatch reports "function not found," which reads like a deploy failure and isn't.

### 6. Teardown

```bash
gcloud functions delete <NAME> --gen2 --region=<REGION>
```

Offer this at the end of any throwaway or demo build. Undeleted functions are how a $0 free-tier experiment quietly becomes a line item — and note that **Artifact Registry and Cloud Build bill separately from Cloud Run**, so a function inside the Cloud Run free tier is not necessarily free.

## Routing table

| Read this | When |
|---|---|
| `references/fit-and-limits.md` | The fit gate is close to the line; the user challenges a disqualification; you need an exact number, a cost model, or a "use X instead" recommendation with a citation |
| `references/event-triggers.md` | Anything not HTTP — Pub/Sub, Cloud Storage, Eventarc. Decorators, deploy flags, local CloudEvent testing, and the at-least-once/idempotency rules that are **mandatory, not advisory** |
| `references/workspace-and-ai-bridges.md` | Connecting a function to Google Workspace (Gmail, Drive, Chat, Sheets, Apps Script, Add-ons) or to Gemini/Vertex AI, or hosting an MCP server on Cloud Run |
| `references/troubleshooting.md` | A deploy fails, a call 403s, logs are empty, or something works locally but not in the cloud |

## Sibling skills

- **python** — the uv loop, type hints, testing, packaging idioms.
- **web-security** — any time auth posture, public exposure, secrets, or input handling comes up. `--allow-unauthenticated` is a security decision.

## Defaults this skill holds

Unless the user says otherwise: Python 3.12, HTTP trigger, `us-central1`, gcloud CLI (reproducible and re-runnable, unlike Console clicks), local-first via the uv loop, and **auth posture surfaced explicitly rather than defaulted silently** — public vs IAM-gated depends on the project and it's not yours to assume.
