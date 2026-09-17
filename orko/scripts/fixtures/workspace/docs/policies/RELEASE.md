# Release Policy

A release tag is cut only after the mechanical gate passes and the judgment items below are confirmed by a human. Each line links to the file that owns the rule; this checklist sequences them and adds nothing.

## Mechanical gate

Run from the workspace root or from `code/`:

```sh
code/scripts/release-check.sh MAJOR.MINOR.PATCH
```

It exits nonzero and lists every failure. It checks that the code release manifest is complete and matches the version, the documentation baseline commit exists, every implemented specification is accepted by a named approver, has a delivery plan and an approved review unless the profile or a recorded waiver exempts them, and passes `spec-check.sh`, the acceptance record names a human and the exact candidate commit, the docs release record exists and matches, both changelogs have an empty Unreleased section, `STATUS.md` is current, and both working trees are clean.

## Deployment and the tag

Acceptance precedes the tag, and the tag precedes production. A pipeline that deploys production on merge to the default branch inverts that order and must not be used. Choose one model and record it in `ARCHITECTURE.md` under Reliability and operations:

| Model | Merge to default branch | Tag push |
| --- | --- | --- |
| Deploy from tags | Integration only; no deployment | Deploys production |
| Staging on merge | Deploys a staging environment where acceptance is performed | Promotes that build to production |

In both models the acceptance record's `candidate_commit` is the commit that was actually exercised, and the tag points at that commit.

## Before tagging, in order

1. Specifications in `code/release/manifest.yaml` `implemented_specs` are `accepted` with `approved_at` set. Amendments made during implementation are recorded. See [`CHANGE-CONTROL.md`](CHANGE-CONTROL.md).
2. The delivery plan's requirement mapping reflects what shipped.
3. A `REVIEW-NNN` names every implemented specification in its `reviews` list, has every finding dispositioned, and has `approved_by` set by a human.
4. `code/docs/testing/README.md` maps each requirement to its evidence.
5. `ARCHITECTURE.md` and `DESIGN.md` are updated if structure or styling changed materially; an ADR exists for any consequential technical choice.
6. `code/CHANGELOG.md` Unreleased entries are moved under the version heading.
7. `code/release/manifest.yaml` is completed and committed. The tag must point at a commit containing it.
8. An `ACCEPT-NNN` record names the candidate commit, a human approver, and a decision of `accepted`.
9. `versions/MAJOR.MINOR/releases/MAJOR.MINOR.PATCH.yaml` is created from the template with the code tag, commit, acceptance record, and included IDs.
10. Waivers for any skipped artifact are recorded in the version README with reason and approver.
11. The mechanical gate passes.

## Tag

```sh
git -C code tag -a vMAJOR.MINOR.PATCH -m "vMAJOR.MINOR.PATCH"
git -C code push origin vMAJOR.MINOR.PATCH
```

## After tagging

1. Set the docs release record `status: released` and `released_at`.
2. Move the version `CHANGELOG.md` Unreleased entries under the release heading.
3. Update the release index in the version README and the latest-release column in `versions/README.md`.
4. Move the work to Recently completed in `STATUS.md` and update `as_of`.
5. Commit the docs repository. This commit may follow the tag; it does not need a circular reference from code.

## Judgment items

The gate cannot decide these. Confirm each explicitly in the release review:

- Architecture and design documents genuinely reflect the shipped system.
- Review findings were dispositioned on merit, not closed to clear the gate.
- Every waiver has a reason a future reader will accept.
- Rollback and migration notes in the plan still hold for the built artifact.
