Direct — set the direction and the goals that everything downstream serves.

---

## Artifact A: Product Strategy One-Pager

### Skeleton

```markdown
# Product Strategy One-Pager

## Product Vision
_A clear, inspiring statement of the product's ultimate purpose and direction._

## Value Proposition
_What core value does this product deliver to its users or market?_

## Strategic Pillars (3-5 key focus areas)
- [Pillar 1]
- [Pillar 2]
- [Pillar 3]

## Target Market & Audience
- [Primary audience segments]
- [Notable market opportunities or gaps]

## Competitive Differentiators
- [Unique features, advantages, positioning vs. competitors]

## Key Metrics for Success
- [Metric 1: strategic progress]
- [Metric 2: market impact]

## 12-Month Strategic Objectives (Summary)
- [Objective 1]
- [Objective 2]

---
_Review and revisit quarterly._
```

### How to Fill

**Product Vision:** Write one sentence that is durable across multiple planning cycles and anchored in user value — not company aspiration. It should describe what the world looks like when the product succeeds, not what the product does mechanically. Avoid superlatives ("best," "leading") with no grounding.

**Value Proposition:** Name the job-to-be-done, the user benefit delivered, and why this product does it better or differently than the next best alternative. One to two sentences; should be legible to someone outside the company.

**Strategic Pillars:** Choose 3–5 focus areas that are mutually distinct and together cover the strategy's full scope. Pillars are thematic (e.g., "Reliability," "Enterprise Onboarding," "Data Ecosystem") — not projects or features. If two pillars feel similar, merge them. Each pillar must map to at least one Key Metric for Success; if a pillar has no metric attached, it is either unmeasurable (reconsider it) or missing a metric (add one).

**Target Market & Audience:** Identify primary segments with enough specificity to inform prioritization decisions. "SMBs" is too broad; "SMBs with 10–50 seats in regulated industries" is usable. Note market gaps or tailwinds that make now the right time.

**Competitive Differentiators:** Be honest. List only advantages that are real, defensible, and visible to buyers. An advantage that exists only internally — speed of iteration, culture — is not a differentiator in this document.

**Key Metrics for Success:** Every metric must be measurable and tied back to at least one pillar. Prefer outcome metrics (retention rate, revenue per user, time-to-value) over activity metrics (features shipped, meetings held).

**12-Month Strategic Objectives (Summary):** State outcomes, not deliverables. "Reach 85% gross retention" not "Launch the new pricing page." These summarize intent; detail moves to OKRs.

### Quality Bar

- [ ] Fits one printed page.
- [ ] Each strategic pillar maps to at least one Key Metric for Success — gaps are blocked.
- [ ] Vision is durable and user-anchored, not a slogan.
- [ ] Differentiators are externally visible and defensible.
- [ ] Objectives are outcomes, not feature lists.
- [ ] Metrics are outcome-based, not activity-based.

### Pitfalls

- **Vision as slogan.** "We empower teams to do more" has no direction; it cannot guide a prioritization call. A good vision creates a decision filter.
- **Overlapping pillars.** "Growth" and "Acquisition" covering the same ground splits attention without adding clarity. One pillar, one distinct theme.
- **Activity metrics masquerading as success metrics.** "Ship 12 features" measures output, not impact. Replace with what happens in the market or for users as a result.
- **Objectives that are feature lists.** "Launch mobile app, redesign onboarding, add SSO" is a roadmap excerpt, not a strategic objective. State the outcome those features are meant to produce.

### Filled Example

```markdown
# Product Strategy One-Pager

## Product Vision
Give operations teams at mid-market companies a single source of truth for revenue data — so they can make decisions in minutes, not days.

## Value Proposition
RevOps teams at 50–500 person companies spend 30–40% of their reporting cycle moving data between disconnected systems. This product eliminates that by connecting CRM, data warehouse, and finance sources into one live workspace — reducing time-to-insight from days to under an hour.

## Strategic Pillars (3-5 key focus areas)
- Data Connectivity — reliable, low-maintenance integrations with the tools RevOps teams already use
- Report Reliability — numbers that are accurate and reproducible without manual reconciliation
- Time-to-Value — new teams producing their first report within one business day of signup

## Target Market & Audience
- Primary: RevOps and Sales Ops analysts at B2B SaaS companies, 50–500 employees
- Secondary: Finance teams at the same companies who consume RevOps outputs
- Opportunity: Mid-market segment is underserved by enterprise BI tools (too complex) and spreadsheet plugins (too brittle)

## Competitive Differentiators
- Pre-built connectors for Salesforce, HubSpot, Stripe, and Snowflake — configured in minutes, not months
- Report templates built for RevOps workflows, not generic BI exploration
- Audit trail showing when source data last refreshed — removes the "which numbers are right" conversation

## Key Metrics for Success
- Data Connectivity: ≥98% integration uptime across all connectors (maps to Data Connectivity pillar)
- Report Reliability: ≤2% of weekly reports require manual correction after delivery (maps to Report Reliability pillar)
- Time-to-Value: Median time from signup to first published report ≤1 business day (maps to Time-to-Value pillar)
- Retention: Gross revenue retention ≥88% at 12 months (maps to all pillars)

## 12-Month Strategic Objectives (Summary)
- Reach 88% gross revenue retention by end of Q4
- Reduce median time-to-first-report from 4 days to under 1 business day by Q3

---
_Review and revisit quarterly._
```

---

## Artifact B: OKRs

### Skeleton

```markdown
# Objectives & Key Results (OKRs)

## Objective 1
_State a qualitative goal (inspire action, focus on value)._

- KR1: [Measurable outcome — SMART]
- KR2: [Measurable outcome — SMART]

## Objective 2
- KR1: [Measurable outcome — SMART]
- KR2: [Measurable outcome — SMART]
```

### How to Fill

**Objectives:** Each objective is qualitative, motivating, and directional — it tells the team what winning looks like this cycle without specifying how to get there. One sentence. Avoid attaching numbers to objectives; numbers belong in key results. Limit to 3–5 objectives per team per quarter; more than that signals a lack of focus, not more ambition.

**Key Results:** Each KR must be SMART — Specific, Measurable, Achievable, Relevant, and Time-bound. Every KR needs a number and a deadline. If you cannot measure it from existing instrumentation or a planned measurement you will build, rewrite it or drop it.

The KR-vs-task distinction is non-negotiable: a KR describes an *outcome* that proves progress toward the objective, not an action the team will take. "Ship the new onboarding flow by March" is a task — it says nothing about whether users benefited. "Increase 7-day activation rate from 41% to 58% by end of Q1" is a KR — it proves onboarding improved. If you find yourself writing "complete," "launch," "ship," or "deploy" in a KR, stop and ask what outcome that action is meant to produce, then write that instead.

Write 2–4 KRs per objective. Fewer keeps focus; more than 4 usually means the objective is too broad or the team is padding.

### Quality Bar

- [ ] Every KR has a numeric target and a deadline.
- [ ] No KR uses task language ("ship," "launch," "complete," "deploy").
- [ ] KRs collectively prove the objective if met — not just correlated with it.
- [ ] Measurable from existing or planned instrumentation.
- [ ] 2–4 KRs per objective.
- [ ] 3–5 objectives total per team per cycle.

### Pitfalls

- **KRs that are tasks.** "Launch mobile app by Q2" is a milestone on the roadmap, not a result. Rewrite to the outcome: "Increase mobile DAU from 0 to 8,000 by end of Q2."
- **Vanity metrics.** Page views, registered users, and app downloads can all rise without the business improving. Use metrics that reflect real engagement or value delivered.
- **Sandbagging.** KRs set so conservatively that achieving them proves nothing. A well-calibrated KR is ambitious enough that hitting all of them would require strong performance, not just execution.
- **Too many objectives.** Six or more objectives per team per quarter means none of them are truly prioritized. Cut to the three that matter most.

### Filled Example

```markdown
# Objectives & Key Results — Q3 2026

## Objective 1
Make onboarding fast and reliable enough that new teams reach value before their first check-in meeting.

- KR1: Median time from signup to first published report drops from 4 business days to under 1 business day by September 30.
- KR2: 7-day activation rate (users who publish at least one report within their first week) rises from 34% to 52% by September 30.
- KR3: Onboarding-related support tickets in the first 14 days fall by 40% relative to Q2 baseline, measured by September 30.
```
