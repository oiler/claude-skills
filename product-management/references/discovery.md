Discover — understand the problem and the people before proposing a solution.

---

## Artifact A: Problem & Hypothesis Statement

### Skeleton

```markdown
# Problem & Hypothesis Statement

## Problem Statement
_Describe the pain point or unmet need._

## Hypothesis Statement
If [we take this action/implement this feature], then [we expect this outcome], because [reason/evidence/rationale].
```

### How to Fill

**Problem Statement:** Name the user, the pain, and the evidence that confirms it's real. No solution language — describe what's broken or missing, not what you plan to do about it. A well-formed problem statement names a specific user segment, a specific friction or unmet need, and a signal (metric, support volume, session data) that proves it matters.

**Hypothesis Statement:** Follow the `If [action], then [measurable outcome], because [rationale]` structure exactly. The "then" clause must be quantified — put a number and a timeframe on it. The "because" must cite a real signal (research finding, analytics, support trend), not a restatement of the action or a gut feeling.

### Quality Bar

- [ ] Problem names a specific user (not "users in general").
- [ ] Problem cites evidence — a metric, a data source, or a named research finding.
- [ ] Problem contains no solution language.
- [ ] "Then" clause is measurable and time-bound (a number, a percentage, a deadline).
- [ ] "Because" cites a real signal, not a guess.
- [ ] Hypothesis is falsifiable — there's a clear way to know if it's wrong.

### Pitfalls

- **Smuggling the solution into the problem.** "Users struggle because we don't have SSO" is a solution statement; "Users abandon at account creation" is the problem.
- **Unmeasurable "then."** "Users will be happier" or "conversion will improve" cannot be verified. Name a metric and a threshold.
- **"Because" that restates the action.** "Because we added SSO" is circular. The "because" must explain the causal mechanism from existing evidence.
- **Single broad problem for multiple segments.** If the pain differs by user type, split it.

### Filled Example

> **Problem:** New users abandon signup at the account-creation step — 38% drop-off in the last 90 days, concentrated on mobile.
> **Hypothesis:** If we add single sign-on, then mobile signup completion rises by 20% within one quarter, because session recordings show password creation is the top abandonment point.

---

## Artifact B: User Persona

### Skeleton

```markdown
# User Persona: [Persona Name]

## Demographics
- Age:
- Gender:
- Location:
- Occupation/Role:
- Education:

## Goals & Motivations
- [What does this user want to achieve?]
- [What motivates them?]

## Pain Points/Challenges
- [Key frustrations, unmet needs, obstacles]

## Behaviors
- [Typical workflows]
- [Preferred channels, devices, interaction methods]

## Quotes (optional)
_"Sample quote that captures this persona's voice or pain point."_

## Needs/Wants
- [What this persona needs from your product]
- [What delights them]

## Key Usage Scenarios
- [Scenario 1]
- [Scenario 2]

## Success Metrics for This Persona
- [What success looks like for this user]
```

### How to Fill

Ground every field in evidence — interviews, analytics, support tickets, observability data. When a field is inferred rather than observed, mark it explicitly (e.g., "inferred — validate in next round of interviews"). Omit demographic fields that have no bearing on product decisions; a field included only to look thorough adds noise.

Cover internal users and stakeholders as well as external customers; the empathy principle applies equally to both. Goals, pains, and behaviors should be specific and observable — "wants to close reports faster" is usable; "wants a better experience" is not. Success Metrics must be measurable and tied to the goals you listed.

Mark the persona as either **validated** (grounded in research with real users) or **hypothesis** (synthesized from indirect signals, to be validated).

### Quality Bar

- [ ] Goals and pain points are specific and observable, not generic.
- [ ] Success metrics are measurable and connected to stated goals.
- [ ] Evidence source cited or field marked as inferred.
- [ ] Persona covers relevant internal users/stakeholders if applicable.
- [ ] Persona is labeled validated or hypothesis.
- [ ] Demographics included only where they influence product decisions.

### Pitfalls

- **Fictional demographics with no decision relevance.** Age and gender rarely change what the product should do; include them only if they demonstrably affect behavior or access.
- **One "average user" masking multiple segments.** If goals and pains diverge across groups, create separate personas rather than averaging them into incoherence.
- **Omitting internal users.** Operations staff, support agents, and internal tooling users are real users with real pain points.
- **Unvalidated persona presented as fact.** Mark hypothesis personas clearly so the team knows to validate before committing to them.

### Filled Example

**User Persona: Maya Chen — Internal Operations Analyst** *(hypothesis — to be validated in Q3 interviews)*

**Demographics**
- Age: 31
- Gender: Female
- Location: Chicago, IL (remote)
- Occupation/Role: Operations Analyst, Revenue Ops team
- Education: Bachelor's, Business Analytics

**Goals & Motivations**
- Produce weekly pipeline and churn reports without manual data wrangling.
- Earn trust from leadership by delivering accurate numbers on tight deadlines.

**Pain Points/Challenges**
- Spends 3–4 hours each Monday pulling data from three disconnected systems before any analysis begins.
- Report formats change with each leadership request; no single template holds.

**Behaviors**
- Works primarily in spreadsheets; moves data between Salesforce, the data warehouse, and Google Sheets by hand.
- Uses desktop; rarely on mobile during work hours.
- Shares finished reports via Slack and email; rarely in the product UI itself.

**Quotes (optional)**
*"By the time I have the numbers ready, the meeting has already started."*

**Needs/Wants**
- A single export or live connection that pulls all three data sources into one place.
- Report templates that survive leadership format changes with minimal rework.

**Key Usage Scenarios**
- Monday morning: pull last week's pipeline data, reconcile against CRM, send to VP of Sales by 9 a.m.
- Month-end: build churn analysis across three cohorts; flag anomalies for the customer success team.

**Success Metrics for This Persona**
- Monday report prep time falls from 3–4 hours to under 45 minutes.
- Zero escalations due to data discrepancies between source systems.
