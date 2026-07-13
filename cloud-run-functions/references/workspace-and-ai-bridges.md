# Bridges — Google Workspace and Gemini/Vertex AI

How a Cloud Run function connects to the rest of Google: Workspace data (Gmail, Drive, Chat, Sheets) on one side, Gemini and Vertex AI on the other.

**The timeout correction that governs this whole page.** Most Workspace bridges deliver through **Pub/Sub**, which makes your function **event-driven** — and event-driven functions cap at **540 seconds (9 minutes)**, not the 60 minutes people quote for gen2. The 60-minute figure is **HTTP-only**. This matters most in exactly the place it's most often cited: "Apps Script has a 6-minute limit, so hand the slow work to a Cloud Run function which allows 60 minutes." That's true *only if the handoff is an HTTP call*. If you route it through Pub/Sub, you traded a 6-minute limit for a 9-minute one.

If the work genuinely needs more than 9 minutes: HTTP-trigger it directly, or use a Cloud Run **job**.

---

## 1. Real-time event bridges (asynchronous)

Workspace tells your function that something happened.

**Google Workspace Events API** — the modern webhook engine. You create a subscription against a Workspace resource (a Drive file, a Chat space, a Meet), and it packages changes as **CloudEvents** and delivers them to a **Pub/Sub topic**. Your function subscribes to that topic.

**Pub/Sub** is the delivery vehicle, which means everything in `event-triggers.md` applies in full: `@functions_framework.cloud_event`, base64-decoded message data, **at-least-once delivery so idempotency is mandatory**, the 9-minute cap, and the **512 KB event size limit**.

**Gmail push notifications** (the `watch` method) — configure a mailbox to publish to Pub/Sub on new message, label change, or thread delete. Same shape, same constraints.

Architecture, end to end:

```
Workspace resource → Workspace Events API → Pub/Sub topic → Cloud Run function
                                                             (cloud_event, ≤9 min, ≤512 KB)
```

That 512 KB ceiling is why you never expect the *document* in the event. The event says "file X changed"; the function then calls the Drive API to fetch it.

## 2. Native UI bridges (user-facing)

Workspace embeds your function in the product surface.

**Google Workspace Add-ons — alternate runtimes.** Add-ons historically had to be written in Apps Script. The Workspace Add-ons API's alternate-runtimes framework lets you host the logic entirely in a Cloud Run function, rendering sidebars, contextual cards, and menus inside Gmail, Calendar, and Drive via JSON card layouts.

**Google Chat apps.** Configure the Chat API to route user messages, card clicks, and space events to an **HTTPS-triggered** Cloud Run function.

Both of these are **HTTP-triggered**, which means: the 60-minute ceiling genuinely applies — *but it's irrelevant*, because a human is waiting. A Chat app that takes 30 seconds is already broken as a product. If the user's request kicks off slow work, acknowledge immediately and hand the work to Pub/Sub, a job, or a task queue. Don't hold the UI open.

## 3. Low-code and compute bridges

**Apps Script → Cloud Run function.** Apps Script is an excellent bridge for macros inside Sheets and Docs, but it has a hard **6-minute** execution limit. The pattern: use Apps Script to gather document context, `UrlFetchApp` the payload to an **HTTP-triggered** Cloud Run function, and map the result back onto the document.

Re-read the top of this page before repeating the "60 minutes" line. The handoff must be **HTTP** for that ceiling to apply, and even then: if the Apps Script call is synchronous, the script is still sitting inside its own 6-minute budget waiting for you. A function that takes 20 minutes doesn't help a caller that dies at 6. Either return fast, or make the handoff asynchronous (function writes to a Sheet / sends a notification when done) and let Apps Script stop waiting.

**AppSheet.** No-code apps over Workspace data. Automation bots can fire a webhook action that invokes a Cloud Run function when data changes. HTTP-triggered; secure it (see below).

## 4. Identity — the invisible glue

**Service accounts and Domain-Wide Delegation.** A service account in your GCP project, granted domain-wide delegation in the Workspace Admin Console, lets the function **impersonate any user in the domain** — write to a user's Sheet, draft mail as a manager, audit file structures — without interactive login.

This is the most powerful bridge and by far the most dangerous. Domain-wide delegation is, in effect, a standing credential to act as anyone in the organization. It deserves a real security conversation, not a config line:

- Scope the delegation to the **narrowest OAuth scopes** that work, never the broad ones.
- Impersonate the **specific user** the request concerns, not a privileged admin, and derive that identity from a trusted source — never from a caller-supplied field.
- A function with DWD and `--allow-unauthenticated` is a **domain-wide privilege escalation endpoint reachable by anyone with the URL.** Never combine them.

Route this to the **web-security** skill whenever it comes up. It is not a Cloud Run question.

## 5. Calling Gemini and Vertex AI from a function

**Zero-key authentication.** Don't manage API keys. Attach a service account to the function and grant it `roles/aiplatform.user` — the Google Gen AI SDK / Vertex AI client picks up credentials from the environment automatically. This is the main reason to put model calls behind a function rather than in a client.

Where a function is a *good* fit for AI work:

- **Orchestration and glue.** Event arrives → function calls Gemini → writes the result somewhere. The function is coordinating, not computing.
- **Backend for Gemini function calling.** Gemini emits a structured tool-call request; your function is the tool that fetches the data. These are short, request-shaped, and exactly what a function is for.
- **MCP server on Cloud Run.** An agent connects over HTTP and discovers tools dynamically. Note this is usually better as a Cloud Run **service** — MCP sessions are long-lived and stream, which fits the service shape, not the function shape.

Where it is **not** a fit — check these against the fit gate:

- **Self-hosted model inference.** Needs a **GPU**, which is documented for Cloud Run services/jobs/worker pools and **not** for functions. Model serving goes in a service.
- **Long multi-model pipelines.** A chain of classify → generate → audit can easily exceed **9 minutes** if it's event-triggered. Chain it in **Workflows**, or run it as a **job**.
- **Streaming tokens back to a user over a long-lived connection.** Technically possible — but bounded by the request timeout and awkward inside the function packaging. Use a service.

**Third-party models** (OpenAI, Anthropic): standard HTTP via `httpx`. Keep tokens in **Secret Manager** and mount them at runtime — never in source, never in an env var committed to a repo.

**Cost note that bites here specifically:** an AI function typically waits on a slow model call, and under request-based billing you pay **active CPU for the whole wait**. Low concurrency plus long model latency is precisely the shape where a function loses to an always-on service. Raise concurrency (the function is I/O-bound, so it can handle many in-flight calls per instance) or reconsider the packaging. See the cost cliffs in `fit-and-limits.md`.

## Sources

The Workspace bridge taxonomy comes from oiler's `bridges.md` research. The limits that constrain it — the 540s event cap, the 512 KB event size, at-least-once delivery, GPU availability, billing shape — come from `fit-and-limits.md`, which is sourced to Google's live docs. **Where the two disagree, the limits win.**
