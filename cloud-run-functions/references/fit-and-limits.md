# Fit and limits — the numbers, with sources

Verified against Google's live docs, July 2026. Every limit carries a source. Where Google's own docs conflict, that's flagged rather than resolved by guessing — an invented number is worse than an acknowledged gap, because the user will build on it.

Note: Cloud Run docs migrated from `cloud.google.com/run/docs/*` to `docs.cloud.google.com/run/docs/*`.

## Contents

- [Timeouts — the HTTP/event split](#timeouts)
- [Memory and CPU](#memory-and-cpu)
- [GPU](#gpu)
- [Concurrency and instances](#concurrency-and-instances)
- [Payload sizes and streaming](#payload-sizes-and-streaming)
- [Filesystem](#filesystem)
- [CPU throttling after response](#cpu-throttling-after-response)
- [Cold starts](#cold-starts)
- [Build and deploy constraints](#build-and-deploy-constraints)
- [Cost model and the cliffs](#cost-model-and-the-cliffs)
- [Databases, VPC, and connections](#databases-vpc-and-connections)
- [The decision table: function vs service vs job vs elsewhere](#the-decision-table)
- [Known gaps in Google's docs](#known-gaps)

---

## Timeouts

**This is the limit that catches the most people, because "gen2 raised the timeout to 60 minutes" is only half true.**

| Trigger | Max timeout | Source |
|---|---|---|
| **HTTP function** | **60 min (3,600s)** | [functions/quotas](https://docs.cloud.google.com/functions/quotas) |
| **Event-driven function** (Eventarc/Pub/Sub/GCS) | **540s — 9 minutes** | [functions/quotas](https://docs.cloud.google.com/functions/quotas) |
| Scheduled / task-queue function | 1,800s (30 min) | [functions/quotas](https://docs.cloud.google.com/functions/quotas) |
| Cloud Run **service** | 60 min max, **5 min default** | [request-timeout](https://docs.cloud.google.com/run/docs/configuring/request-timeout) |
| Cloud Run **job** task | **168 hours (7 days)**; 1 hour with GPU | [run/quotas](https://docs.cloud.google.com/run/quotas) |

The gen1 9-minute cap did **not** go away for event triggers. It lifted for HTTP only. Anyone porting a long Pub/Sub handler to gen2 expecting 60 minutes is wrong, and will find out in production under load rather than in testing.

Beyond 15 minutes Google warns you must implement retries and tolerate client reconnection — there's no guarantee the same instance handles the retry. Timeout expiry returns **504** and closes the connection, but **the instance keeps running** and can interfere with subsequent requests.

**Always return a response.** A function that hangs runs to timeout and **you are billed for the entire timeout window** — a hung 60-minute HTTP function is a 60-minute bill.

## Memory and CPU

| | Value | Source |
|---|---|---|
| Max memory | **32 GiB** | [run/quotas](https://docs.cloud.google.com/run/quotas), [memory-limits](https://docs.cloud.google.com/run/docs/configuring/services/memory-limits) |
| Max CPU | **8 vCPU** | [cpu](https://docs.cloud.google.com/run/docs/configuring/services/cpu) |
| Default memory | 512 MiB services / **256 MiB functions** | [memory-limits](https://docs.cloud.google.com/run/docs/configuring/services/memory-limits) |
| Default CPU | 1 vCPU | [cpu](https://docs.cloud.google.com/run/docs/configuring/services/cpu) |

**Memory is constrained by CPU** — you don't pick them independently ([cpu](https://docs.cloud.google.com/run/docs/configuring/services/cpu)):

| vCPU | Memory range |
|---|---|
| 0.08 | ≤ 512 MiB |
| 0.5 | ≤ 1 GiB |
| 1 | ≤ 4 GiB |
| 2 | ≤ 8 GiB |
| 4 | 2–16 GiB |
| 6 | 4–24 GiB |
| 8 | 4–32 GiB |

**Fractional CPU (<1 vCPU) is a trap.** It silently forces three things: concurrency **must be 1**, billing **must be request-based**, and the execution environment **must be first generation**. A "cheap" 0.5-vCPU function is a concurrency-1 gen1-sandbox function — and per the cost section below, concurrency-1 is the *expensive* shape. The saving is illusory.

**⚠ Documented conflict.** The [comparison page](https://docs.cloud.google.com/run/docs/functions/comparison) says functions cap at "16 GiB RAM with 4 vCPU". [run/quotas](https://docs.cloud.google.com/run/quotas), the config pages, and [functions/quotas](https://docs.cloud.google.com/functions/quotas) all say 32 GiB / 8 vCPU. Best reading: **16 GiB/4 vCPU is the ceiling exposed through the Cloud Functions v2 API surface; 32 GiB/8 vCPU is what the underlying Cloud Run service supports.** No page reconciles them. Treat >16 GiB on a function as unverified — if the user needs that much, recommend a service and sidestep the question.

## GPU

**Not documented for functions.** GPU is documented for Cloud Run **services**, **jobs**, and **worker pools** ([gpu](https://docs.cloud.google.com/run/docs/configuring/services/gpu)). The functions comparison table has no GPU row and the GPU GA announcement doesn't mention functions.

Whether you can attach a GPU to the Cloud Run service *underlying* a deployed function is **unconfirmed** — mechanically plausible since it's the same resource, but no doc says so. Don't build a plan on it.

If the workload needs a GPU: **Cloud Run service.** Available types are NVIDIA **L4** (24 GB VRAM; min 4 CPU / 16 GiB) and **RTX PRO 6000 Blackwell** (96 GB VRAM; min 20 CPU / 80 GiB). One GPU per instance, sidecars can't touch it, requires instance-based billing, still scales to zero, instances start in ~5s.

## Concurrency and instances

| | Value | Source |
|---|---|---|
| Max concurrent requests/instance | **1,000** | [about-concurrency](https://docs.cloud.google.com/run/docs/about-concurrency) |
| Default concurrency (gcloud) | **80 × vCPU count** | [about-concurrency](https://docs.cloud.google.com/run/docs/about-concurrency) |
| Concurrency, **gen1** | **1**, not configurable | [comparison](https://docs.cloud.google.com/run/docs/functions/comparison) |
| Default max instances | **100 per revision** | [max-instances](https://docs.cloud.google.com/run/docs/configuring/max-instances) |
| Max instances ceiling | No fixed number — derived from regional CPU/memory quota ÷ per-instance allocation | [max-instances-limits](https://docs.cloud.google.com/run/docs/configuring/max-instances-limits) |
| Default min instances | **0** | [min-instances](https://docs.cloud.google.com/run/docs/configuring/min-instances) |

Google recommends starting **event-driven** services at **max 3 instances** and tuning up ([max-instances-limits](https://docs.cloud.google.com/run/docs/configuring/max-instances-limits)) — event sources can fan out hard and a runaway function is both a cost and a downstream-database event.

Google also warns: "**Avoid low concurrency settings**, which limit instance reuse during traffic spikes and increase cold start frequency." Concurrency-1 functions cold-start constantly by construction.

**Unconfirmed:** the default concurrency for *event-driven* functions specifically. Services default to 80×vCPU; Google's own FaaS pricing example models concurrency 1. If it matters, set it explicitly rather than inheriting.

## Payload sizes and streaming

| | Limit |
|---|---|
| HTTP/1 request | **32 MiB** |
| HTTP/2 request | no limit |
| HTTP/1 response | **32 MiB** (unchunked) |
| Function HTTP response | 32 MB non-streaming / **10 MB streaming** |
| **Eventarc event** | **512 KB** (10 MB for legacy events) |
| Open connections/instance | 50,000 |
| Outbound connections | 700/s, 5,000/min (excludes Direct VPC) |

Source: [run/quotas](https://docs.cloud.google.com/run/quotas), [functions/quotas](https://docs.cloud.google.com/functions/quotas).

**The 512 KB Eventarc cap is the sharp edge** — 64× smaller than the HTTP limit. Event-driven functions cannot receive large payloads. The pattern is: the event carries a **GCS object pointer**, the function fetches the object. If someone is designing an event that embeds a file, stop them here.

**Streaming** ([container-contract](https://docs.cloud.google.com/run/docs/container-contract), [websockets](https://docs.cloud.google.com/run/docs/triggering/websockets)):
- Streaming HTTP responses: supported, no config, send `Transfer-Encoding: chunked`.
- **WebSockets: supported** — but a WebSocket **is an HTTP request** and is bound by the request timeout. Max connection life = your timeout ceiling. SSE is the same story.
- HTTP/2 and gRPC end-to-end: supported; HTTP/2 is off by default (Cloud Run downgrades to HTTP/1 to the container unless enabled).

These are Cloud Run capabilities, so they *do* apply to functions — but the 9-minute event cap makes long-lived streaming a services-only pattern in practice.

## Filesystem

From the [container runtime contract](https://docs.cloud.google.com/run/docs/container-contract): "It is an **in-memory file system**, so writing to it uses the instance's memory. Data written to the file system doesn't persist when the instance stops."

- `/tmp` is **tmpfs and consumes your memory limit.** The "32 GiB writable filesystem" figure in the quotas page is just the memory ceiling restated, not a separate allowance.
- You can **OOM-crash the instance by writing files.** Google recommends an in-memory volume with a configured size limit as a guard rail.
- Files **can persist between invocations on a warm instance** ([functions-best-practices](https://docs.cloud.google.com/run/docs/tips/functions-best-practices)). A leaked temp file is a slow memory leak that only manifests under sustained warm traffic — i.e. never in your testing.
- **No persistent disk.** Google's own fit criteria require "no local persistent file system" ([fit-for-run](https://docs.cloud.google.com/run/docs/fit-for-run)).
- **Volume mounts work** — GCS (Cloud Storage FUSE), NFS/Filestore, in-memory, secrets, Cloud SQL. Functions best practices explicitly points functions at them for persistent data.

## CPU throttling after response

**The single most common Cloud Run functions bug.** Two billing modes ([cpu-allocation](https://docs.cloud.google.com/run/docs/configuring/cpu-allocation)):

- **Request-based (default, and the default for functions):** charged only while processing requests, starting, and shutting down. **CPU is throttled to ~zero the moment you return the response.**
- **Instance-based:** charged for the entire instance lifecycle. CPU always allocated; background threads keep running.

Google's [general tips](https://docs.cloud.google.com/run/docs/tips/general) is blunt: "When the Cloud Run service finishes handling a request, the instance's access to CPU will be disabled or severely limited. **You shouldn't start background threads or routines that run outside the scope of the request handlers**."

And [functions-best-practices](https://docs.cloud.google.com/run/docs/tips/functions-best-practices): background work after return "cannot access CPU resources… they interfere with subsequent invocations and **commonly cause connection reset errors**."

This is where `asyncio.create_task(...)` without an await, fire-and-forget cleanup, and "I'll just log this after I respond" all die. The failure is *non-local*: the symptom appears as a connection reset in a **later** invocation on the same warm instance, which makes it brutal to debug from the symptom backward.

Fixes, in order of preference: do the work **before** returning; move it to a **worker pool** or **job**; or switch to instance-based billing.

**Startup CPU boost** temporarily raises CPU during startup (base 0–1 vCPU → 2; base 2 → 4; base 4+ → 8). It's a service setting, so it applies to functions, and Google recommends it for cold starts.

Also: **never call `sys.exit()`** in a function. And **port 25 (SMTP) is blocked** — use an email API.

## Cold starts

- Startup timeout: **4 minutes per instance**; exceed it and the instance is killed ([run/quotas](https://docs.cloud.google.com/run/quotas)).
- Levers Google names: **startup CPU boost**, **min instances**, **lean dependencies**, **global-scope caching**, **lazy init**.
- "We recommend setting a minimum number of instances, and completing initialization at load time, **if your application is latency-sensitive**."

**Google does not publish a typical cold-start latency figure.** Any millisecond number you've seen is community benchmarking, not an SLA. Don't quote one as fact — if the user is latency-sensitive enough to care, the answer is "measure it for your dependency graph, and set min-instances if it's not good enough."

## Build and deploy constraints

| | Value |
|---|---|
| Source archive (deploy without build) | ≤ **250 MiB** |
| Build machine | Cloud Build default, **e2-standard-2** |
| Build timeout | 60 min default |
| Container image size | no direct limit |
| **Functions per project/region** | **1,000 minus the number of Cloud Run services deployed** |
| Env vars | 1,000 per container, 32 KB each |
| **Admin API writes** | **60 per 60 seconds — CANNOT be increased** for gen2 |

Note the function count: **functions and services share one 1,000-slot pool.** They are the same resource. And the 60-writes-per-minute admin quota is the one that bites CI/CD pipelines deploying many functions in parallel.

**Buildpacks** ([deploying-source-code](https://docs.cloud.google.com/run/docs/deploying-source-code)):
- A `Dockerfile` in the source dir is used **instead of** buildpacks.
- **No documented mechanism for apt/system packages.** Need `ffmpeg`, `libvips`, `poppler`, a native lib? Write a Dockerfile — and once you have a Dockerfile you're a Cloud Run **service**, not a function. This is the cleanest practical dividing line between the two.
- Buildpacks set source file mtime to **Jan 1, 1980** for reproducibility, which **breaks browser cache validation for static files** served from the image. Non-obvious, real.

## Cost model and the cliffs

All rates us-central1, list, from [cloud.google.com/run/pricing](https://cloud.google.com/run/pricing). **Functions bill identically to services.**

**Request-based (default for functions):**

| Resource | Rate |
|---|---|
| CPU active | $0.000024 / vCPU-s |
| CPU idle (min-instances only) | $0.0000025 / vCPU-s |
| Memory active | $0.0000025 / GiB-s |
| **Requests** | **$0.40 per million** |
| Free tier | 180k vCPU-s + 360k GiB-s + 2M requests/mo |

**Instance-based (always-on CPU):**

| Resource | Rate |
|---|---|
| CPU | $0.000018 / vCPU-s |
| Memory | $0.000002 / GiB-s |
| **Requests** | **none — no per-request fee** |
| Free tier | 240k vCPU-s + 450k GiB-s/mo |
| Minimum billing | 1 min per instance lifetime |

**Worker pools** are the cheapest continuous-compute shape in Cloud Run: CPU $0.000011244/vCPU-s, ~38% below instance-based.

### The four cliffs worth knowing

1. **Concurrency is the dominant lever.** Google's own example: 10M requests × 400ms × 1 vCPU / 512 MiB — **concurrency 20 → $13.69/mo; concurrency 1 → $81.72/mo.** A 6× swing from one setting. And fractional CPU *forces* concurrency 1.

2. **Instance-based CPU is 25% cheaper than request-based active CPU** ($0.000018 vs $0.000024) **and has no $0.40/M request fee.** Google: "For services with steady, slowly varying traffic, consider instance-based billing. The savings… **outweigh the cost of paying for idle time**."

3. **When does a function lose to an always-on service?** An always-on 1-vCPU instance-based instance ≈ **$47/mo** in CPU, no request fee. A request-based function costs $0.000024/vCPU-s of *active* time + $0.40/M requests. The function wins until roughly **1.97M vCPU-seconds of active compute/month — about a 22% duty cycle at 1 vCPU.** Past that, plus the request fee above a few million requests, the "cheap serverless function" is the expensive option.

4. **Min-instances bill idle time; ordinary idle instances don't.** One always-warm 1-vCPU / 512 MiB min-instance ≈ **$6.50–8/mo**. Cheap for one — but it multiplies by min-instance count **and by revision during rollouts**.

**Hidden charges:** Cloud Build, **Artifact Registry storage**, and **Eventarc** all bill separately from Cloud Run. Google says it outright: you can incur charges "**even when your use of Cloud Run falls within the free tier**." A free-tier function is not necessarily a free function.

## Databases, VPC, and connections

**Cloud SQL** ([connect-run](https://docs.cloud.google.com/sql/docs/mysql/connect-run)):
- **Cloud Run instances are limited to 100 connections to a Cloud SQL database** — per instance. Multiply by max-instances: 100 instances × a 10-connection pool = 1,000 connections, which will exhaust a Cloud SQL instance trivially. **Cap max-instances and size pools to 1–2 connections per instance.** This is the classic serverless-meets-database blowup.
- Google's fix at scale is **Managed Connection Pooling**.
- Set `cloudSqlRefreshStrategy` to **`lazy`** in serverless — otherwise the connector's background refresh thread collides with CPU throttling (see above).
- Private IP requires **Direct VPC egress** or a Serverless VPC Access connector.

**VPC egress** ([connecting-vpc](https://docs.cloud.google.com/run/docs/configuring/connecting-vpc)):
- **Direct VPC egress is Google's recommendation for new deployments** — lower latency, scales to zero, pay only for egress, per-service firewall rules. Several per-instance connection quotas *exclude* Direct VPC traffic.
- **Serverless VPC Access connectors bill as always-on Compute Engine VMs**, share network tags across services, and lag during traffic surges.
- Tradeoff: Direct VPC autoscales more slowly (new VPC NICs) and consumes more IPs.

**In-memory caching:** global-scope caching is recommended and works — but it's **per-instance and never shared**. No cross-instance cache exists. Anything that must be coherent goes in Memorystore/Redis. With concurrency >1, mutable globals need locks.

## The decision table

Google's framing ([what-is-cloud-run](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)):

| Resource | Use when | Timeout ceiling |
|---|---|---|
| **Function** | Single-purpose handler, no container needed, glue/event code | 60 min HTTP / **9 min event** |
| **Service** | Websites, APIs, microservices, streaming, AI inference, GPU, anything needing a Dockerfile | 60 min |
| **Job** | Runs to completion, doesn't serve requests — migrations, scripts, batch, model training | **7 days** |
| **Worker pool** | Pull-based, non-HTTP — Kafka consumers, Pub/Sub **pull** subscriptions | none (no request) |

**Choose a service over a function when any of:** >9 min on an event path · apt/system packages · GPU · >16 GiB or >4 vCPU · background work after response · long-lived WebSocket/gRPC streams · receive payloads over 512 KB on the event path.

**Choose a job when:** the work runs to completion and doesn't serve requests, or exceeds 60 minutes.

**Choose a worker pool when:** you want a Pub/Sub **pull** subscription — no request timeout to fight, no HTTP surface to secure. This is the most under-used escape hatch and the right answer surprisingly often.

**When to leave Cloud Run entirely.** Google's fit criteria: serves HTTP/HTTP2/WebSockets/gRPC *or* runs to completion; **no local persistent filesystem**; horizontally scalable; ≤8 CPU / ≤32 GiB ([fit-for-run](https://docs.cloud.google.com/run/docs/fit-for-run)). Miss any one and the answer is GKE, Compute Engine, Batch, or App Engine.

**Adjacent services Google names:**
- **Cloud Tasks** — explicit invocation where the publisher retains full control: scheduling, **rate-limiting calls to a fragile database or third-party API**, dedup, retries, smoothing spikes, delegating slow work off the user's request path.
- **Pub/Sub** — *implicit* invocation; the publisher doesn't know or control the consumers. That's the clean one-line distinction from Cloud Tasks.
- **Cloud Scheduler** — cron.
- **Workflows** — orchestrating multiple HTTP services with step ordering and output passing, when latency matters.
- **Cloud Composer/Airflow** — batch orchestration that tolerates seconds of inter-task delay. Not for low latency.
- **Batch** — long-running compute jobs. Google's named pattern is Workflows managing the lifecycle of Batch jobs.

## Known gaps

Be honest about these rather than filling them in:

| Item | Status |
|---|---|
| Function max memory/CPU: 16 GiB/4 vCPU vs 32 GiB/8 vCPU | **Documented conflict** between Google's own pages |
| GPU on a function's underlying service | **Unconfirmed** — no doc says yes or no |
| Default concurrency for event-driven functions | **Unconfirmed** — set it explicitly |
| Typical cold-start latency (ms) | **Not published by Google.** Don't quote a number as fact |
| apt/system packages via buildpacks | **No documented mechanism** — treat as unsupported |
| Dataflow as a stated alternative | **Not found** in the Cloud Run docs |
