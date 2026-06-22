Learn — close the loop: capture what happened and feed it back into the next Discover.

---

## Retrospective / Postmortem

### Skeleton

```markdown
# Retrospective / Postmortem Report

## Project or Sprint Name:
[Name or identifier]

## Date:
[YYYY-MM-DD]

## Participants:
[Roles/names]

## Goals & Scope Recap
- [Restate intended goals or outcomes]

## What Went Well?
- [Successes, wins]

## What Didn't Go Well?
- [Problems, blockers, missed expectations]

## Lessons Learned
- [Key takeaways]
- [Process insights]

## Action Items & Owners
| Action Item      | Owner  | Due Date   | Status   |
|------------------|--------|------------|----------|
| [Follow-up task] | [Name] | YYYY-MM-DD | [Status] |

## Additional Comments
[Anything else — appreciations, feedback]
```

### How to Fill

**Goals & Scope Recap:** Restate the sprint or project goals as written at kickoff — not how you remember them now. This is the yardstick for everything that follows. "Went well" and "didn't go well" are meaningless without a clear reference point.

**What Went Well / Didn't Go Well:** Describe outcomes in terms of systems and process, not individuals. "Our deployment pipeline had no rollback step" is actionable; "Alex forgot to add the rollback" assigns blame without generating learning. When a person's decision contributed to an outcome, describe the conditions that led to that decision — what information was available, what the process allowed, what the incentive was.

**Lessons Learned:** Each lesson must be specific enough to change behavior. "Communicate earlier" is too vague — name the specific gap: "We didn't surface the dependency on the data team until sprint day 3; next sprint we'll map external dependencies in planning." If a lesson doesn't point to a concrete change, keep digging.

**Action Items & Owners:** Every lesson produces at least one action item. Each action item requires a named owner (a person, not a team) and a specific due date. "TBD" is not a due date. Action items identified here feed directly back into the next Discover cycle — they may reopen a problem statement, trigger new user research, or revise a process. Name that linkage explicitly where it applies.

### Quality Bar

- [ ] Goals recap restates original scope, not a post-hoc version.
- [ ] Observations focus on systems and process, not individuals.
- [ ] Every lesson has at least one action item.
- [ ] Every action item has a named owner (a person) and a due date.
- [ ] At least one action item names the next-cycle artifact it feeds into (problem statement, research plan, etc.).
- [ ] Lessons are specific — tied to a named event, metric, or decision point.

### Pitfalls

- **Blame.** Naming individuals as causes of failure closes down learning. The retro's job is to surface conditions that led to the outcome, so the system can be improved.
- **Lessons with no action items.** A lesson that doesn't produce a change is just venting. If you can't name what changes next time, the lesson isn't done yet.
- **Vague takeaways.** "We need to communicate better" is the most common dead-end in retros. Push to the specific: what was not communicated, to whom, at what point, and what process change prevents the gap.
- **No link to the original goals.** "What went well" is empty without the goals recap as a baseline. Teams that skip the recap often celebrate the wrong things or miss real misses.
- **No closed loop.** The retro is not a terminal document — it is the input to the next cycle. If none of the action items connect to Discover (research, hypothesis revision, problem restatement), check whether the real lessons were captured.

### Filled Example

```markdown
# Retrospective / Postmortem Report

## Project or Sprint Name:
Sprint 14 — Mobile Onboarding v2

## Date:
2026-06-20

## Participants:
Product Manager, iOS Engineer, Android Engineer, UX Designer, QA Lead

## Goals & Scope Recap
- Ship revised mobile onboarding flow (SSO + reduced field count) to 100% of new mobile signups.
- Target: reduce mobile signup drop-off from 38% to under 20% within 30 days of launch.

## What Went Well?
- SSO integration shipped on time with zero auth-related bugs in production.
- QA and engineering ran parallel tracks effectively — no blocking handoff delays.

## What Didn't Go Well?
- Android release was delayed two days because the play store review process wasn't accounted for in the sprint plan.
- Drop-off metric is tracking at 27% at day 10 — ahead of the 38% baseline but short of the 20% target.

## Lessons Learned
- The sprint planning template has no field for app store review windows; teams default to assuming same-day release.
- Early funnel data suggests the email-verification step (not SSO) is now the top drop-off point — the original hypothesis addressed only password friction.

## Action Items & Owners
| Action Item | Owner | Due Date | Status |
|---|---|---|---|
| Add "store review lead time" field to sprint planning template | Priya (PM) | 2026-06-27 | Open |
| Open new Problem Statement for email-verification friction; hand off to Discover | Priya (PM) | 2026-06-27 | Open |

## Additional Comments
Strong team execution on a technically complex sprint. The missed target reflects a hypothesis gap, not a delivery failure — the team shipped exactly what was planned.
```
