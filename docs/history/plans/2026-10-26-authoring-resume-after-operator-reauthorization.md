# Plan: Resolve the post-reauthorization authoring stop

Backlog origin: `docs/history/backlog/2026-10-25-authoring-stopped-after-reauthorization.md`
Driving force: efficiency + code-quality
Plan review record: the staging series `.ai-playbook/reviews/2026-10-26-plan-review-authoring-resume-after-operator-reauthorization-p95b6d19c-r*.md` (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.0h total, largest task 0.5h
Authoring claim: `docs/tmp/authoring-claims/authoring-resume-after-operator-reauthorization.md` (session `01a1638f-189d-7b02-9cf8-0990eb6f3dfd`)

## Terms

- **Fresh review:** a review launched from the exact current plan bytes with its source digest re-derived and usage minted before launch.
- **Same-root recurrence:** a fresh review reopens the root issue that reconciliation already addressed.
- **Origin:** `docs/history/backlog/2026-10-25-authoring-stopped-after-reauthorization.md`.

## Why

The origin records that an authoring session stopped after explicit operator authorization even though the safe route was to mint usage, launch a fresh review of the revised plan, and continue under the existing review limits. The source plan later received a fresh r14 review and completed. This plan verifies whether the stop exposed a contract gap across the three named instruction owners or was an execution lapse, then records the narrow result and closes the origin.

## Gist & Examples

Title: Resolve the post-reauthorization authoring stop
TLDR: Verify the existing continuation rules and close the incident with a narrow evidence-backed disposition, for efficiency and code-quality.
Before: The origin treats the stop as a possible cross-skill contract gap while the revised source plan has a later r14 review.
After: The completed plan records the r13-to-r14 evidence, the rule ownership comparison, and whether one byte-neutral clarification is warranted; it closes only this origin.
Edge cases: Preserve mint-before-launch, current-digest review, the caller-owned review handoff, the configured round and budget limits, and the stop if the same root returns after a fresh review.

## Outcome

Record whether the stop arose from an instruction gap or execution noncompliance, and close the origin using the source plan's review-time evidence.

- Reconstruct r13 and r14 against their review-time source bytes; do not compare a review digest directly to the later archived plan bytes.
- Trace explicit reauthorization, fresh-review ownership, digest checks, and recurrence stops to the current Blocker recovery, review-reconciliation, and review-plan rules.
- Change one owning skill only if a concrete handoff gap remains; keep the edit byte-neutral and add no gate or review attempt.
- Complete the origin through the operator-directed archive: move it to `docs/history/backlog/completed/` with the covered flip and retain it there; the existing origin gate recognizes that completed archive state.

Gate delta: none; no gate, refusal class, fence, protocol layer, schema field, or review duty is added or removed, and no dispatch condition changes.

## Assumptions

- The backlog row's cited episode is the scope of record; the completed source plan and its review artifacts are historical evidence and remain unchanged.
- The existing Blocker recovery rule authorizes safe continuation after explicit direction, while review-reconciliation and review-plan own fresh-review and recurrence boundaries.
- The current r14 artifact is the latest source-plan review record; its review-time digest must be checked against the corresponding pre-archive source bytes because the completed twin has later archival changes.
- No external owner, deployment, or runtime change is required.
- A skill-text change is included only if execution proves the current handoff incomplete; any operative text growth is offset by equivalent deletion in the same change.

Decision points requiring a grill: none remain; the operator-provided repository rule selects the backlog completed archive for landed-plan origins, and the origin gate recognizes an archived completed row.
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Standing constraints

- Do not alter the completed source plan, its historical review records, review counters, round budgets, validators, review-agent catalogs, or stop rules.
- Do not treat r13 as current certification or r14 as evidence for the superseded scope; bind each verdict to its recorded source digest.
- Do not ask for another authorization after the existing explicit direction; stop only if the authorized route reveals a new material decision or the same root returns after a fresh review.
- Do not add a new gate, retry, counter, or review round.

## Evaluation Criteria

**Quality dimensions:**
- Evidence accuracy: the incident chronology, source digests, and review verdicts agree with the archived plan and staging artifacts.
- Contract clarity: each continuation and stop condition has one current owner and remains unchanged unless a specific gap is demonstrated.
- Scope control: only the named origin and, if necessary, one owner-level skill span change.

**Done when:**
- The final disposition is supported by the review-time source bytes, r13/r14 records, and all three current instruction surfaces.
- If no contract gap remains, no operative skill text changes; if one is proven, one concise byte-neutral clarification lands at its owner.
- The origin row is retained under `docs/history/backlog/completed/` with the required covered flip and this plan as witness; the plan's readiness and hygiene checks pass.

**Ship when:** None; this is a repository-local instruction and backlog disposition.

## Review Scope

**Explicit must-fix:** any finding that misstates the r13/r14 timeline, treats archive bytes as review-time bytes, attributes a continuation or stop rule to the wrong skill, or widens the origin's scope.

**Documentation:**
- `AGENTS.md` (review-only)
- `docs/history/backlog/2026-10-25-authoring-stopped-after-reauthorization.md` (Task 2)
- `docs/history/backlog/completed/` (Task 2)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `agents/skills/review-reconciliation/SKILL.md` (Task 2)
- `agents/skills/review-plan/SKILL.md` (Task 2)

**Read-only evidence:**
- `docs/history/plans/completed/2026-10-25-done-finalize-checkpoint-manifest-env-honoring.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r13.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r13.stats.json` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r14.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r14.stats.json` (review-only)

**Out of scope; reject unless plan-related:** review-agent catalog changes, generic review-loop redesign, changes to completed history, and any additional backlog item.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-26-authoring-resume-after-operator-reauthorization.md
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-26-authoring-resume-after-operator-reauthorization.md
bash scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-26-authoring-resume-after-operator-reauthorization.md
```

### Task 1: Reconstruct the incident and compare the owning rules

Context surface: the origin, source-plan history, r13/r14 review records, and the three instruction owners named in the origin; record the result in this plan and keep the completed source plan and historical review artifacts read-only.

Files:
- `docs/history/backlog/2026-10-25-authoring-stopped-after-reauthorization.md`
- `docs/history/plans/completed/2026-10-25-done-finalize-checkpoint-manifest-env-honoring.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r13.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r13.stats.json` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r14.md` (review-only)
- `.ai-playbook/reviews/2026-10-25-plan-review-done-finalize-checkpoint-manifest-env-honoring-p00814e0c-r14.stats.json` (review-only)
- `agents/skills/maintenance/decisions.md`
- `agents/skills/review-reconciliation/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [ ] Re-derive the review-time source bytes and show why the current completed-plan bytes differ from the r14 digest; verify r13 is stale for the revised scope and r14 is the later fresh result. [class: IMPLEMENTATION_REQUIRED]
- [ ] Map explicit authorization, safe continuation, fresh caller-owned review, and same-root recurrence stop to their current owning clauses; record any concrete gap or confirm the rules already close the route. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve the historical review and source-plan artifacts; record the evidence and disposition in this plan. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: record reauthorization continuation disposition` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Apply only a proven clarification and close the origin

Context surface: Task 1's evidence and this plan's Standing constraints; no additional surface is in scope.

Files:
- `AGENTS.md` (read-only authority)
- `docs/history/backlog/2026-10-25-authoring-stopped-after-reauthorization.md`
- `docs/history/backlog/completed/`
- `agents/skills/maintenance/decisions.md` (only if it is the demonstrated owner)
- `agents/skills/review-reconciliation/SKILL.md` (only if it is the demonstrated owner)
- `agents/skills/review-plan/SKILL.md` (only if it is the demonstrated owner)

- [ ] If all three rules already direct the authorized fresh-review route, make no operative text change and record the incident as execution noncompliance. [class: IMPLEMENTATION_REQUIRED]
- [ ] If a specific handoff gap remains, add one concise clarification at its owning skill, delete equivalent bytes in that same change, and preserve every digest, mint, budget, round, and recurrence boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Move the origin row to `docs/history/backlog/completed/` with `Status: covered (<completed plan path>)` and `Covered by:` naming this plan; retain the archived row and make no other row or catalog edits. The existing origin gate recognizes a matching completed-archive row. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: close reauthorization authoring stop origin` [class: IMPLEMENTATION_REQUIRED]
