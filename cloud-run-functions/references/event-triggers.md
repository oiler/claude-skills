# Event triggers — Pub/Sub, Cloud Storage, Eventarc

HTTP is the default path because it has no source to provision and no Eventarc IAM to untangle. Everything here is the branch you take when something *else* has to invoke the function.

**Before you write any of this, re-check two limits** (full detail in `fit-and-limits.md`):

- **540 seconds. Nine minutes.** Event-driven functions are hard-capped there — the 60-minute gen2 timeout is HTTP-only. If the handler might exceed 9 minutes, it belongs in a Cloud Run job or a worker pool, and you should say so now rather than after it's built.
- **512 KB per event.** The event carries a *pointer* (a GCS object name, a row ID), never the payload itself. If someone is designing an event that embeds a file, that's the design bug.

## The shape of it

| | HTTP | Pub/Sub | Cloud Storage | Generic (Eventarc) |
|---|---|---|---|---|
| Decorator | `@functions_framework.http` | `@functions_framework.cloud_event` | `@functions_framework.cloud_event` | `@functions_framework.cloud_event` |
| Handler arg | `request` (Flask Request) | `cloud_event` | `cloud_event` | `cloud_event` |
| Deploy flag | `--trigger-http` | `--trigger-topic=<TOPIC>` | `--trigger-bucket=<BUCKET>` | `--trigger-event-filters="type=..."` |
| Verify by | `curl` the URL | publish a message, read logs | upload an object, read logs | fire the source event, read logs |
| Extra APIs | — | `pubsub`, `eventarc` | `eventarc` | `eventarc` + the source's API |
| Timeout ceiling | 60 min | **9 min** | **9 min** | **9 min** |

Extra APIs to enable:

```bash
gcloud services enable eventarc.googleapis.com pubsub.googleapis.com
```

## Handler

An event handler takes a CloudEvent and returns nothing. There's no response to shape — acknowledgement is signalled by *not raising*.

```python
import base64

import functions_framework


@functions_framework.cloud_event
def on_message(cloud_event):
    event_id = cloud_event["id"]              # your idempotency key — see below
    data = cloud_event.data["message"]["data"]
    payload = base64.b64decode(data).decode()
    print(f"{event_id}: {payload}")           # stdout lands in Cloud Logging
```

Pub/Sub message data arrives **base64-encoded** inside `cloud_event.data["message"]["data"]`. Forgetting the decode is the first thing everyone gets wrong.

Cloud Storage events look different — `cloud_event.data` carries `bucket`, `name`, `metageneration`, etc. The object *content* is not in the event; fetch it from GCS by name.

## Provision the source first

The trigger binds to something that must already exist. Deploy will fail otherwise.

```bash
gcloud pubsub topics create <TOPIC>

gcloud functions deploy <NAME> --gen2 --runtime=python312 --region=<REGION> \
  --source=. --entry-point=on_message --trigger-topic=<TOPIC>
```

Trigger binding **can take several minutes** to become active after a successful deploy. A message published immediately after deploy may go nowhere — that's not a bug, it's propagation. Also: **one function binds to exactly one trigger.** You cannot attach a second.

## Testing locally

functions-framework serves event functions over HTTP — you POST a CloudEvent envelope at it and simulate the source.

```bash
uv run functions-framework --target=on_message --signature-type=cloudevent --debug
```

Then, for a Pub/Sub event (`Hello` → base64 `SGVsbG8=`):

```bash
curl localhost:8080 \
  -H "Content-Type: application/json" \
  -H "ce-id: 1234" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/P/topics/T" \
  -d '{"message":{"data":"SGVsbG8="}}'
```

This is worth doing. The alternative — deploying and publishing real messages to find out you forgot the base64 decode — is a five-minute round trip per attempt.

## At-least-once delivery: idempotency is mandatory

Google guarantees **at-least-once** execution per event. **Duplicates will happen.** Not "might under exotic failure" — they are part of the contract, and a handler that assumes exactly-once will double-charge a card, double-send an email, or double-insert a row eventually.

The event ID is your idempotency key. Google's named techniques:

- Use the **event ID** (`cloud_event["id"]`) as an idempotency key.
- **Check state inside a database transaction** before mutating.
- **Persist processed event IDs** and skip ones you've seen.

```python
@functions_framework.cloud_event
def on_message(cloud_event):
    event_id = cloud_event["id"]
    if already_processed(event_id):   # inside the same txn as the mutation
        return
    do_the_work(cloud_event)
    mark_processed(event_id)
```

## Retries — the default differs by how you deployed

This is a genuine footgun, and it's invisible from the code:

| Deployed via | Retry default |
|---|---|
| **Cloud Run Admin API** | **Enabled, and cannot be disabled** |
| **Cloud Functions v2 API** (`gcloud functions deploy`) | **Disabled**; opt in with `--retry` |

So the same handler has different failure semantics depending on which surface deployed it. Check, don't assume.

Retry mechanics:
- Ack semantics: HTTP **2xx = ack**; **4xx/5xx = retry**. An unhandled exception is a retry.
- Eventarc retains messages **24 hours**, exponential backoff **10s → 600s**.
- **The retry window expires after 24 hours.**

**Defend against the infinite-retry loop.** A poison event that always fails will retry for the full 24 hours, burning invocations and money. Google's own recommendation is to **filter on the event timestamp and discard events older than a threshold**:

```python
import datetime

MAX_AGE = datetime.timedelta(seconds=60)


@functions_framework.cloud_event
def on_message(cloud_event):
    ts = datetime.datetime.fromisoformat(cloud_event["time"])
    age = datetime.datetime.now(datetime.timezone.utc) - ts
    if age > MAX_AGE:
        print(f"dropping event {cloud_event['id']}, age {age}")
        return          # ack and give up — do not raise
    do_the_work(cloud_event)
```

The instinct is to make the handler robust so it never poisons. The point of this guard is that it will anyway, and you want a bounded blast radius when it does.

## Scaling: cap it

Google recommends starting event-driven functions at **max 3 instances** and tuning up. An event source can fan out far harder than human traffic, and the downstream database is usually what fails first — not the function.

```bash
gcloud functions deploy <NAME> --gen2 ... --max-instances=3
```

Pair this with the Cloud SQL connection math in `fit-and-limits.md`: instances × pool size is your real connection count, and Cloud Run caps at 100 connections to Cloud SQL *per instance*.

## When the event path is the wrong path

Reach for a **worker pool** with a Pub/Sub **pull** subscription instead of a push-triggered function when:

- the handler needs longer than 9 minutes,
- you want to control your own consumption rate rather than being pushed at,
- or you'd rather not expose an HTTP surface at all.

Worker pools have no request timeout to fight and are the cheapest continuous-compute shape in Cloud Run. This is the most under-used escape hatch in the whole product surface, and it's the right answer more often than people reach for it.
