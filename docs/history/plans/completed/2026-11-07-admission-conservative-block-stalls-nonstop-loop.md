# Plan: recurring audit dispatch supplies complete write paths

Backlog origin: docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
Driving force: efficiency
Plan review record: .ai-playbook/reviews/2026-11-08-plan-review-admission-conservative-block-stalls-nonstop-loop-p48ac8271-r*.md (highest fresh ready=yes round for the current source digest)
Execution budget: 1h total, largest task 1h
Executed: yes (b9853a1e937df36d6f8bd4796ca3e448ff15243c)
Authoring claim: 2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (session sess_edd477e1-e097-4cbc-a973-7ace838d677c)

## Terms

- Audit dispatch: a due recurring task whose registry kind is audit, including the deferred-retriage task whose id is deferred-retriage.
- Candidate write set: the complete set of repository-relative paths the selected task may write during its dispatched run.
- Incomplete write set: a write path that cannot be determined before admission from the task procedure and current run inputs.
- Claim-keyed recovery: the landed outstanding-side fix that seeds each execution claim's admission record from its covering plan's Files lists (scripts/execution_claim.sh take); it supplies outstanding-run evidence, not candidate write sets.
- User-directed override: the interactive-session rule in agents/skills/maintenance/guards.md that lets a live-user-directed session proceed past a deferral-class guard trip on a verified-disjoint surface; it covers interactive deferrals, not audit dispatch inputs.

## Why

The claim-keyed outstanding-manifest recovery landed in commit 57817a38f. That makes this plan's proposed covering-plan composition and recovery exception obsolete. The interactive deferral used in the motivating turn is also already covered by the user-directed override in agents/skills/maintenance/guards.md; this plan must not duplicate that rule.

The remaining candidate-side gap is recurring audit dispatch. The admission CLI accepts explicit, repeatable --owned-path operands and refuses an empty candidate set, but the maintenance contract does not define how an audit task supplies its write paths. An audit task has no plan Files list from which the caller can derive those paths. Passing an empty or partial set either keeps a disjoint task parked or understates its collision surface.

## Gist & Examples

TLDR: derive each eligible audit task's complete write set through the existing --owned-path input and keep incomplete sets refused; why: efficiency.

Before: a plan dispatch derives candidate paths from Files lists, but a recurring audit dispatch has no corresponding candidate-set rule.

After: a due audit task with a finite, precomputable write set passes every exact path to the existing admission consult; the final-slot check derives the set again. A genuine intersection still refuses.

Edge cases: read-only inputs are excluded; task state and report paths are included when written; a dynamic target is resolved before admission when possible; a fresh final-slot refusal resolves D3 and leaves the task due for a later survey; pending_dispatch retention wording applies only to an already-retained target or the carrier-refusal path that actually writes the record; a consult invoked with no candidate source is the CLI tool_error path, not a refusal pass. deferred-retriage remains kind=audit, not a new registry kind.

## Outcome

The admission consult admits a recurring audit task only when its complete write set is known and disjoint from every outstanding run.

- Finite audit write paths pass through the existing explicit operand.
- Intersections, unknown paths, and empty sets keep the existing refusal; a freshly refused audit target resolves D3 and stays due for a later survey, and only an already-retained pending_dispatch target or the carrier-refusal path writes retention.
- Claim-keyed outstanding evidence and the other lane and quota decisions stay unchanged.

Gate delta: none - this plan supplies complete inputs to the existing consult; it adds no gate, refusal, checked surface, state field, or schema.

## Assumptions

- check_admission already accepts repeatable --owned-path operands; scripts/dispatch_admission.py is unchanged.
- A task's procedure and resolved state-file path are the write-surface source. Include only paths the run may write, not read-only task files or source files.
- A task with a conditional or dynamic output is eligible only when the concrete path can be derived before the final-slot consult. Otherwise retain the existing refusal; never submit a convenient subset.


- The runtime occupancy and quota-reset issues remain tracked separately by docs/history/backlog/2026-11-08-maintenance-capacity-aware-chaining.md and docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md.

Decision points requiring a grill: none remain.

## Standing constraints

- Preserve exact-set intersection, empty-set refusal, and conservative handling of unknown or malformed evidence.
- Re-derive the candidate write set at the final-slot check; do not reuse stale inputs.
- The consult is read-only and serializes nothing: the state file children[] registration write is when the run becomes visible to later consults (an outstanding children[] entry is an --outstanding-without-manifest operand), and the consult-to-registration interval holds the accepted residual interleaving window per state-file.md's targeted-edit drift rules, recovered by the listing-based lane arms and the same-task in-flight guard. The operative wording states this boundary truthfully and the interleaving witness demonstrates that recovery path, never an exclusion.
- Do not change the peer-run record, admission script, lane guard, quota policy, or retry-carrier behavior.

## Evaluation Criteria

**Quality dimensions:** correctness, loop liveness for disjoint finite audit tasks, and maintainability.

**Done when:**
- The maintenance instructions derive a complete audit candidate write set and pass each path through the existing operand.
- The existing CLI test cases already witness disjoint admission, intersection refusal, and empty-set refusal; the test delta is the audit-derived-set rehearsal only.
- The maintenance pin suite verifies the caller and final-slot wording.
- The origin row records which earlier arms were superseded, already covered, or completed here.

**Ship when:** none; all outcomes are repository-verifiable.

## Documentation Impact Assessment

Update the maintenance admission invariant, scheduling precondition, recurring-task consult, and existing machinery note in place. Update the origin row's per-arm dispositions at completion. No README change is needed because the skill catalog and invocation do not change.

## Review Scope

**Explicit must-fix:** findings on the paths below are always in scope.

**Maintenance instructions:**
- agents/skills/maintenance/SKILL.md (Task 1)
- agents/skills/maintenance/scheduling.md (Task 1)
- agents/skills/maintenance/survey-arms.md (Task 1)

**Machinery note and tests:**
- scripts/machinery_registry.json (Task 1)
- scripts/check_maintenance_pins.sh (Task 1)
- scripts/test_dispatch_admission.py (Task 1)

**Origin disposition:**
- docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md (Task 1)

**Plan-related extension:** implementation and review may change files not listed above when the change is required by an explicit task or fixes a regression introduced by this plan. Otherwise reject.

**Out of scope; reject unless plan-related:**
- scripts/dispatch_admission.py, because its existing explicit path operand already implements the needed set comparison.
- agents/skills/maintenance/decisions.md and agents/skills/maintenance/zcode.md, because this plan does not change lane selection or runtime scheduling primitives.
- quota-reset wake, recurrence promotion, and clocked-order execution; each has separate backlog coverage.

## Validation Commands

```bash
env -u PINS_RECORDED_RED_REGISTER -u PINS_RECORDED_RED_AS_OF bash scripts/check_maintenance_pins.sh
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_dispatch_admission.py -q
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
python3 scripts/plan_readiness.py docs/history/plans/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md
```

### Task 1: derive exact recurring-audit write paths for admission

Context surface: Terms, this task, and Standing constraints.

Files:
- agents/skills/maintenance/SKILL.md
- agents/skills/maintenance/scheduling.md
- agents/skills/maintenance/survey-arms.md
- scripts/machinery_registry.json
- scripts/check_maintenance_pins.sh
- scripts/test_dispatch_admission.py
- docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md

Primary class anchors:
- `check_admission` in `scripts/dispatch_admission.py`

- [x] The admission invariant defines a complete audit candidate write set from the selected task procedure and resolved state path; it includes only paths the run may write and passes each through repeatable --owned-path [class: IMPLEMENTATION_REQUIRED]
- [x] The final-slot consult re-derives that complete set; an unresolved or incomplete path set keeps the existing refusal (the fresh-versus-retained resolution is owned by survey-arms.md's audit-kind retention arm, referenced by name, never restated), never a partial-set pass [class: IMPLEMENTATION_REQUIRED]
- [x] The operative wording states the truthful boundary: the consult is read-only and serializes nothing; the children[] registration write makes the run visible to later consults; the residual interleaving window is recovered by the listing-based lane arms and the same-task in-flight guard [class: IMPLEMENTATION_REQUIRED]
- [x] The interleaving witness demonstrates that recovery path, never an exclusion [class: REPOSITORY_TEST]
- [x] The recurring-task wording identifies deferred-retriage's registry kind as audit within the closed registry kind set, reading the pre-existing retriage-kind phrase as the pending-dispatch target class it already names in survey-arms.md's Pending dispatch paragraph, never a new registry kind [class: IMPLEMENTATION_REQUIRED]
- [x] End-to-end caller witness, rehearsal-fixture form: a test applies the documented derivation steps to a fixture audit task procedure and passes the derived set through the CLI [class: REPOSITORY_TEST]
- [x] The witness derives every path the fixture procedure may write and supplies that complete set at both the pre-dispatch and final-slot consults, with the collision asserted on a secondary output so a hand-picked subset cannot pass [class: REPOSITORY_TEST]
- [x] Pins cover the caller and final-slot contracts; the CLI verdict classes (disjoint pass, intersect refusal, empty-set refusal) are already witnessed by the existing test_dispatch_admission.py cases and are cited as satisfying, the pytest delta scoped to the new audit-derived-set rehearsal only [class: REPOSITORY_TEST]
- [x] The machinery_registry.json admission note is updated in place, the affected registry entry cited as the witness [class: IMPLEMENTATION_REQUIRED]
- [x] The origin row records the covering-plan composition and recovery-exception arms as superseded by the landed claim-keyed recovery, the interactive fallback as already covered by guards.md, and audit candidate derivation as completed here [class: IMPLEMENTATION_REQUIRED]
- [x] The origin's lane-scoping and in-session-continuation arm is dispositioned separately, defaulting to a tracked residual naming its owning backlog [class: IMPLEMENTATION_REQUIRED]
- [x] An already-covered citation is recorded only after verifying it against the cited rule's operative steps: D1's claimed-top-target skip-and-continue is exec-lane candidate scanning with the same conservative verdict for underivable sets, and the guards.md user-directed override is interactive-only while the origin's witnessed mandate is the unattended loop; neither covers the unattended authoring/audit lane-scoping class, so the residual route is expected [class: IMPLEMENTATION_REQUIRED]
- [x] Run the listed validation commands and commit as maintenance: derive complete recurring-audit admission paths [class: IMPLEMENTATION_REQUIRED]


## Disposition of migrated backlog items

Origin row docs/history/backlog/2026-11-07-admission-conservative-block-stalls-nonstop-loop.md deleted by this execution landing; its per-arm disposition follows.

## Disposition (execution 2026-11-08)

Per-arm disposition of the origin's asks, recorded at execution:

- **Covering-plan composition arm and recovery-exception arm: superseded.** The claim-keyed outstanding-manifest recovery landed (the admission record seeded from the covering plan's Files: lists at claim take, merged monotone at done boundaries, read beside done-session manifests; registry entry `script:dispatch_admission.py`'s Outstanding-manifest recovery delta). The interim composition and recovery-exception arms were never landed; this execution deletes neither because neither exists in the operative text.
- **Interactive fallback (in-session deferral route): already covered.** The user-directed override for interactive sessions in `agents/skills/maintenance/guards.md` covers the interactive deferral the motivating turn used (witnessed again 2026-11-08 by this execution's own landing-gate override proceed). No new text.
- **Audit candidate write-set derivation: completed here.** The maintenance instructions now derive a due audit-kind task's complete write set (state record path plus the task body's report, row-move, and filing write targets; read-only inputs excluded), pass each through the existing repeatable `--owned-path` operand, and re-derive at the Step 5 final slot; an incomplete or empty set keeps the existing refusal and pending-dispatch behavior (survey-arms.md Recurring-task registry consult bullet; scheduling.md Step 5 precondition; SKILL.md Invariants consult clause; machinery registry admission note).
- **Lane-scoping and in-session-continuation arm: tracked residual (default route).** Neither D1's claimed-top-target skip-and-continue (exec-lane candidate scanning, the same conservative verdict for underivable sets) nor the interactive-only user-directed override covers the unattended authoring/audit lane-scoping class over the source-less outstanding residual. The residual rides the sibling row docs/history/backlog/2026-11-07-dispatch-admission-manifest-less-outstanding-conservative-global-block.md.
