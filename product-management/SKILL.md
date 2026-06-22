---
name: product-management
description: Generate clear, people-first product management artifacts and apply oiler's product operating principles. Use when writing or refining a PRD or product requirements document, problem statement, hypothesis, OKRs or objectives and key results, product strategy one-pager, roadmap, milestones or project plan, RACI or roles and responsibilities matrix, user persona, or retrospective/postmortem. Triggers on "write a PRD", "product requirements", "define the problem", "frame a hypothesis", "draft OKRs", "product strategy", "roadmap", "milestones", "RACI", "roles and responsibilities", "user persona", "retro", "postmortem", "product brief", "product spec", "as a PM", "product management". Produces a tailored draft immediately, then refines. Output is human-facing and concise; external prose (announcements, emails) routes to the writing-style skill instead.
---

# Product Management

Generate **people-first** PM artifacts — concise, clear, and tailored to the context already on the table. PM is a craft for humans; the artifact serves the reader, not a process.

## The lens (always applies)

PM is a **loop, not a line: Discover → Direct → Deliver → Learn → (back to Discover).** Every artifact is a checkpoint in that loop, never a terminal deliverable.

Carry these into every artifact:
- **User-centric** — lead with who we serve and why it matters to them.
- **Measurable** — every goal carries success criteria; flag any that can't be measured.
- **Incremental** — smallest step that delivers value; break big bets down.
- **Owned** — one accountable owner per outcome.
- **Evidence-driven** — combine qualitative insight with quantitative data.
- **Closed-loop** — build in how the work will be evaluated and revisited.

Full lens, with the rigor we carry from building with AI coding agents: `references/principles.md`.

## Generate-first — how to respond

1. **Identify the artifact** from the request. If ambiguous, pick the best fit and say which.
2. **Pull context** from the conversation and repo. Do **not** interrogate the user.
3. **Missing critical context?** Make a reasonable assumption, mark it `[ASSUMPTION]`, and draft anyway.
4. **Produce the full tailored artifact** — concise, human-facing.
5. **Apply the quality bar inline** and flag weak spots (e.g. "KR2 isn't measurable — suggest a target %").
6. **Offer one round of targeted refinement** only *after* the draft exists.

Never run a menu or step-by-step wizard. Draft first, refine second.

## Routing — artifact → reference

| You're asked for… | Stage | Read |
|---|---|---|
| Problem statement, hypothesis, user persona | Discover | `references/discovery.md` |
| Product strategy one-pager, OKRs | Direct | `references/strategy.md` |
| PRD, milestones/roadmap, RACI | Deliver | `references/delivery.md` |
| Retrospective, postmortem | Learn | `references/learning.md` |

Each reference gives the artifact: a fill-in skeleton, how to fill it, a quality bar, pitfalls, and a worked example. Load only the reference you need.

## Voice

Artifacts use a neutral, professional voice — not personal prose. If the user wants an external-facing announcement, launch email, or marketing copy in their own voice, that's the `writing-style` skill's job, not this one.
