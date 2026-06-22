Deliver — turn direction into a plan people can execute and be accountable for.

---

## Artifact A: PRD

### Skeleton

```markdown
# Product Requirements Document (PRD)

## TL;DR
_A concise summary of the problem, solution, and value._

### Problem Statement
_What problem are we solving?_

### Goals & Objectives
- [Goal 1]
- [Goal 2]

### Target Users / Personas
- [Persona 1]
- [Persona 2]

### Features & Requirements
- [Feature 1: requirement/spec, priority]
- [Feature 2: requirement/spec, priority]

### Success Metrics
- [Metric 1: how success is measured]
- [Metric 2: how success is measured]

### Out of Scope
- [Non-goal]

### Milestones & Timeline
- [Milestone 1 (date, owner)]
- [Milestone 2 (date, owner)]
```

### How to Fill

**TL;DR:** Write this last, but place it first. Three to five sentences that let a busy stakeholder understand the problem, the proposed solution, and the expected value without reading further. Skimmable — no jargon.

**Problem Statement:** Link to the discovery artifact (Problem & Hypothesis Statement or user research). Name the user, the pain, and the signal. No solution language here.

**Goals & Objectives:** State the desired end-state — the outcome the product achieves for users — not the activities the team will perform. "Reduce report prep time from 3 hours to under 45 minutes" is an objective; "build a reporting dashboard" is an activity.

**Features & Requirements:** Each entry carries: what the feature does, its priority (P0/P1/P2 or MoSCoW), and — critically — **objective acceptance criteria**: a detectable, testable condition that tells the team (or an AI coding agent) when the requirement is met. "Done" must be something anyone can verify without asking the author. If you cannot write an acceptance criterion, the requirement is not yet defined.

**Success Metrics:** Measurable outcomes only — a number, a rate, a threshold, a deadline. Outputs (features shipped, meetings held) do not belong here.

**Out of Scope:** Non-empty, always. Make explicit what the team is not doing. Every item left out of scope prevents a future scope-creep argument.

**Milestones & Timeline:** Each milestone names a date and a single owner. Use the Milestones Plan artifact (Artifact B) for the full table; summarize key gates here.

### Quality Bar

- [ ] Every feature entry has objective acceptance criteria — a detectable, testable "done" the team can verify without interpretation.
- [ ] Goals and objectives state the desired end-state (outcome), not just activity.
- [ ] Success metrics are measurable outcomes with a number and a timeframe — not outputs or activities.
- [ ] Out of Scope is non-empty and explicit.
- [ ] Each milestone in the timeline carries a date and a named owner.
- [ ] Problem Statement links to a discovery artifact or names a specific evidence signal.

### Pitfalls

- **Features with no acceptance criteria.** A list of features without criteria hands the definition of "done" to whoever happens to be reviewing the build. This is where scope drift and agent misexecution begin.
- **Success metrics that are outputs.** "Ship v2 of the onboarding flow" measures delivery, not impact. Replace with what changes for users as a result.
- **Empty Out of Scope.** Leaving it blank signals the team didn't think about boundaries. Stakeholders will fill the gap with assumptions.
- **"Done" left to interpretation.** Vague requirements ("improve performance," "better error messages") have no stopping condition. Specify the threshold.
- **Activity objectives.** "Build the data pipeline" is not a goal — it is a task. State what state the world is in when the work succeeds.

### Filled Example

```markdown
# Product Requirements Document (PRD)

## TL;DR
Operations analysts at mid-market B2B SaaS companies spend 3–4 hours each Monday moving data between Salesforce, a data warehouse, and Google Sheets before any analysis begins. This PRD covers a unified data workspace that eliminates manual transfers. Success: median Monday prep time falls from 3–4 hours to under 45 minutes within one quarter of launch.

### Problem Statement
Internal RevOps analysts cannot produce weekly pipeline reports without manually reconciling three disconnected data sources. Session observation and support tickets confirm the reconciliation step is the primary time sink (3–4 hours/week per analyst). See Discovery: Problem & Hypothesis Statement 2026-05.

### Goals & Objectives
- Reduce median weekly report prep time from 3–4 hours to under 45 minutes.
- Eliminate data-discrepancy escalations caused by mismatched source exports.

### Target Users / Personas
- Maya Chen — Internal Operations Analyst (primary; see Persona 2026-05)
- VP of Sales — report consumer; blocked when numbers are late or inconsistent

### Features & Requirements
- **Live CRM Connector (P0):** Pull Salesforce opportunity data on demand.
  - Acceptance criteria: A connected Salesforce account refreshes pipeline data in ≤90 seconds with zero manual export steps. Data matches Salesforce native report within a 0.1% variance threshold on a standard test dataset.
- **Report Template Library (P1):** Pre-built templates for pipeline, churn, and month-end reports.
  - Acceptance criteria: A new user can generate a complete pipeline report from a connected data source in ≤10 minutes without documentation.

### Success Metrics
- Median Monday report prep time ≤45 minutes by end of Q3 2026 (measured via in-product session timing).
- Weekly reports requiring manual correction ≤2% of total reports published (measured via support ticket tagging).

### Out of Scope
- Direct integration with legacy on-premise ERP systems.
- Custom chart builder or ad-hoc BI exploration beyond provided templates.
- Mobile native app.

### Milestones & Timeline
- MVP connector live: 2026-07-15, Maya R. (Eng Lead)
- Template library in beta: 2026-08-01, Dana K. (PM)
- GA release: 2026-09-01, Dana K. (PM)
```

---

## Artifact B: Project Milestones Plan

### Skeleton

```markdown
# Project Milestones Plan

| Milestone        | Description                  | Date       | Owner       | Status  |
|------------------|------------------------------|------------|-------------|---------|
| Kickoff          | Project start                | YYYY-MM-DD | [Name/team] | Planned |
| Design Complete  | User journeys & designs done | YYYY-MM-DD | [Name/team] | Planned |
| MVP Launch       | First deliverable released   | YYYY-MM-DD | [Name/team] | Planned |
| GA Release       | General Availability         | YYYY-MM-DD | [Name/team] | Planned |
```

### How to Fill

**Milestone:** Name the outcome, not the activity. "Design Complete" names a verifiable state; "work on design" names a process. Each milestone should be answerable with a yes/no: either the outcome is reached or it is not.

**Description:** One sentence clarifying exactly what "done" means for this milestone. If a milestone requires a demo, a sign-off, or a measurement threshold to be considered complete, say so here.

**Date:** Use real dates (YYYY-MM-DD), not relative offsets ("week 6"). Dates without a grounding assumption behind them create false precision — note the assumption if the date is an estimate.

**Owner:** A single person, not a team. One named individual is accountable for whether the milestone is reached on the committed date. Teams do the work; one person owns the outcome.

**Status:** Use only: Planned / In progress / Done / Blocked. Keep it current — a status column that is never updated becomes noise.

**Sequencing:** MVP precedes GA. Always. Any sequence where GA appears without a prior MVP milestone should be flagged as a risk.

### Quality Bar

- [ ] Every milestone has a named owner (single person) and a real date.
- [ ] Milestones are outcomes or verifiable states — not activities or phases.
- [ ] MVP milestone exists and precedes GA.
- [ ] Status values are from the fixed set (Planned / In progress / Done / Blocked).
- [ ] Descriptions clarify the "done" condition for any milestone that is not self-evident.

### Pitfalls

- **Activity rows.** "Work on design" or "development sprint" describe effort, not outcomes. A milestone table full of activities gives no signal on whether the project is on track.
- **Ownerless milestones.** "Engineering team" is not an owner. When no individual is accountable, accountability is diffuse and slippage is invisible until it is too late.
- **Dates with no basis.** A date pulled from thin air is a placebo. If the date is an estimate, say so and name the key assumption (dependency, capacity, external factor).
- **Skipping MVP.** Going straight from development to GA removes the feedback loop. Even an internal or limited MVP provides signal before a full public release.

### Filled Example

```markdown
# Project Milestones Plan — Unified Data Workspace

| Milestone        | Description                                              | Date       | Owner    | Status      |
|------------------|----------------------------------------------------------|------------|----------|-------------|
| Kickoff          | Team aligned on scope, personas, and success metrics     | 2026-06-02 | Dana K.  | Done        |
| Design Complete  | User journeys reviewed and approved by PM and one user   | 2026-06-23 | Priya M. | In progress |
| MVP Launch       | CRM connector live for 3 beta users; prep time measured  | 2026-07-15 | Maya R.  | Planned     |
| GA Release       | All connectors and templates live; success metrics met   | 2026-09-01 | Dana K.  | Planned     |
```

---

## Artifact C: RACI Matrix

### Skeleton

```markdown
# Roles & Responsibilities (RACI Matrix)

| Task/Decision        | Responsible | Accountable | Consulted    | Informed     |
|----------------------|-------------|-------------|--------------|--------------|
| Define requirements  | PM          | PM          | Dev, Design  | Exec Sponsor |
| UX Design            | Designer    | Designer    | PM           | Dev          |
| Develop MVP          | Engineer    | Eng Lead    | PM, QA       | Stakeholders |
| Launch/Go-to-Market  | PM          | PM          | Marketing    | All Teams    |
```

### How to Fill

**Responsible (R):** Who does the work. May be more than one person per row.

**Accountable (A):** Who owns the outcome — the person who answers if it goes wrong. **Exactly one Accountable per row, no exceptions.** Multiple A entries on a single row mean no one is actually accountable. If you are tempted to list two names under A, pick the one who would be called into the debrief if the task failed.

**Consulted (C):** Two-way exchange — these people give input before or during the work and expect a response. If their input does not change the outcome, move them to Informed.

**Informed (I):** One-way communication — these people receive updates but do not shape the outcome. Default to Informed when someone needs awareness but not a voice.

Keep rows to real decisions and critical tasks. A RACI that lists every sub-task becomes unreadable and stops being used. Focus on the decisions where ownership is genuinely ambiguous or contested.

### Quality Bar

- [ ] **Exactly one Accountable (A) per row — the single-A rule.** No row has zero A; no row has two or more A.
- [ ] Responsible (R) is present for every row.
- [ ] Consulted (C) is genuinely two-way — these people's input can change the outcome.
- [ ] Informed (I) is one-way — awareness only, no decision influence.
- [ ] Rows cover decisions and critical tasks, not every granular sub-task.

### Pitfalls

- **Multiple Accountables per row.** The most common RACI failure. Two names under A means ownership is shared — which means it is not owned. Cut to one, even if it is politically uncomfortable.
- **No Accountable.** An empty A column is worse than a wrong A. It signals that no one has claimed the outcome.
- **Confusing Consulted with Informed.** Consulted people give input that can change the work; Informed people receive status. Promoting someone to Consulted who will never actually change anything adds noise and sets false expectations.
- **Row explosion.** A RACI with 40 rows covering every sub-task is not used in practice. Limit to decisions and handoffs where confusion is likely.

### Filled Example

The skeleton rows below demonstrate the single-A rule: each row has exactly one person in the Accountable column.

```markdown
# Roles & Responsibilities (RACI Matrix) — Unified Data Workspace

| Task/Decision        | Responsible      | Accountable | Consulted        | Informed         |
|----------------------|------------------|-------------|------------------|------------------|
| Define requirements  | PM               | PM          | Eng Lead, Design | Exec Sponsor     |
| UX Design            | Designer         | Designer    | PM               | Engineering      |
| Develop MVP          | Engineering      | Eng Lead    | PM, QA           | All Stakeholders |
| Launch/Go-to-Market  | PM               | PM          | Marketing        | All Teams        |
| Security Review      | Security Analyst | Eng Lead    | PM               | Exec Sponsor     |
```

Note the "Security Review" row: Engineering does the work (R = Engineering), but the Eng Lead is the single Accountable (A) — the person who would own a post-incident debrief if a vulnerability shipped.
