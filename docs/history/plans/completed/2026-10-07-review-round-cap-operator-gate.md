# Plan: operator checkpoints at the review round cap and mid-loop

Backlog origin: docs/history/backlog/2026-10-06-review-round-cap-operator-gate.md
Driving force: automation (the plan removes recurring manual direction: the operator's 2026-10-06 instruction to pause and reflect at three to four cycles and before any cap closure becomes loop machinery that runs itself, and a pipeline step that still needs the operator to remember it is the debt this plan retires; the operator ask the machinery creates is the sanctioned human decision point, not manual direction)
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-review-round-cap-operator-gate-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-review-round-cap-operator-gate.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- cap boundary: the moment a review loop reaches its configured round cap without a clean round (standard class: round 5), where the cap-closure terminal shape is available.
- operator ask: the loop-stopping presentation of the per-round finding trajectory (staged counts, severities, and the new-root, fold-defect, and wording split from the sidecars' `extensions.convergence`) together with the three choices (continue with cap closure, extend by a stated number of rounds, or park the plan); in an unattended lane the ask parks the plan and reports, never silently closes.
- mid-loop checkpoint: the pause after three to four completed review-fix cycles that presents the concise convergence reflection and asks whether the operator authorizes any scope extension before continuing.
- workflow reflection: the terminal record's paragraph naming which defect classes the rounds staged, whether they converge round over round, and which authoring-time or fold-time check would have front-loaded each class, rendered from the `extensions.convergence` data every round sidecar already carries.
- non-convergence signal: new-root findings not decreasing across two consecutive rounds; it may trigger the operator ask before the cap.
- round-fix cycle: one complete staged review whose accepted blocking findings are amended into the plan.

## Why

The plan 2026-10-06-land-squash-quoted-porcelain consumed all five review rounds on 2026-10-06 without a human in the loop: its fourth-round certification was invalidated by a post-seal em-dash miss and its folds generated the next rounds' findings, so the cap was spent partly on the authoring workflow's own defects, and no step of the loop asked the operator; the cap-closure shape that terminates non-clean loops likewise has no human step. Separately, the operator directed a reflection and scope-extension check after every three to four cycles, and the loop had no checkpoint that could prompt it. The cap exists to stop non-converging reviews, and the operator is the only party who can adjudicate what the rounds' findings evidence; this plan puts that adjudication into the machinery instead of leaving it to be remembered.

## Outcome

The review loop pauses for the operator at the checkpoint, at any non-convergence signal, and at the cap boundary, and its terminal record carries the workflow reflection.

- After three to four completed review-fix cycles the loop pauses and presents the concise convergence reflection with the scope-extension question before any further round launches.
- At the cap boundary the loop stops and presents the operator ask with the trajectory; cap closure runs only on the operator's recorded choice, and an unattended lane parks the plan and reports instead of closing silently.
- The terminal round's staging record carries the workflow-reflection paragraph rendered from the existing `extensions.convergence` data; no new collection exists.

Gate delta: three checked-condition-set growths on existing protocol items (the plans skill's cap-closure rule and review-plan's cap-closure mirror each gain the operator ask before closure runs, plus the mid-loop checkpoint beside the convergence-telemetry rule) and one review-layer duty whose violation blocks (the workflow-reflection paragraph in the terminal record, whose own text carries the witness: the operator's 2026-10-06 direction recorded in the origin row's Origin and Finding fields, and the witnessed five-round spend with no operator ask on plan 2026-10-06-land-squash-quoted-porcelain); the guard liveness ledger's catch-to-incident ratio is 12:14 at authoring time (`python3 scripts/gate_liveness_ledger.py show`, re-derived 2026-10-07), cited per the ledger-citation duty; no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed.

## Assumptions

- assume the arms land in the plans skill's Plan Quality Gate rules (the round loop, convergence telemetry, and cap-closure owner) and review-plan's Iteration Discipline mirror, and that neither review-loop nor review-staging needs edits: review-loop owns the code-review loop, not the plan-review loop this origin targets, and the `extensions.convergence` shape is defined in the plans skill's convergence-telemetry rule and carried by every round sidecar; basis: the plans skill's rules 8, 12, 13, and 16, review-plan's Iteration Discipline rule 8, and the origin row's Fix shape paragraph, re-derived at authoring time; the origin's surface list names all three skills, and this trace reassigns the arms to where the round lifecycle actually lives.
- assume the ask is presentation-plus-stop, not a new refusal class: the loop halts before the cap-closure step and surfaces the ask through the session's user channel; an unattended lane parks and reports exactly as the round-cap operator-gate doctrine the operator already ratified applies manually (backlog row docs/history/backlog/2026-10-06-review-round-cap-operator-gate.md and the 2026-10-06 landing dd2ebc6c); basis: the origin's Outcome paragraph for the ask and its three choices; the origin does not specify unattended behavior, so the park-and-report arm carries the operator-ratified round-cap doctrine's authority (the 2026-10-06 landing dd2ebc6c in this repository's git history, re-derivable via `git log --format=%H dd2ebc6c`, and this session's manual application of it), not the origin's.
- assume cap closure remains available and byte-identical when the operator chooses it: this plan adds the ask before the shape, never altering the closure mechanics, the sidecar shape, or the personal-class limit (the personal-class stop at three with simplify-or-rewrite is untouched); basis: the origin's Fix shape and the plans skill's rule 16 closing sentence.
- assume the reflection renders from `extensions.convergence` (new_root, fold_defect, wording counts per round) with no new telemetry: the origin's Notes for promotion says arm (b) is a rendering duty over existing data; basis: the plans skill's rule 12 and the origin's Notes paragraph.
- assume the mechanical fixture is pins rows plus span gates over the prescribed prose, and no validator gate is added: the origin's class line says process-gate design with no production surface, and its driving force is operator visibility, not enforcement machinery; basis: the origin row's Class and Driving force fields.

Decision points requiring a grill: none remain.

## Standing constraints

- The cap-closure terminal shape, the sidecar schema, and the personal-class limit stay byte-identical; the plan adds only the asks and the reflection.
- The mid-loop checkpoint and the cap ask present data that already exists in the sidecars; nothing in the plan adds collection, telemetry, or a new ledger.

## Gist & Examples

TLDR: The review loop asks the operator at three-to-four cycles, at non-convergence, and at the cap, and its terminal record reflects on the workflow (automation).

**Before (today):** A plan's review loop hits round 5 without a clean round, and the cap-closure shape dispositions the residuals into the plan and lands it, silently. Nobody asks whether the five rounds measured plan complexity or the authoring workflow's own defects, and the operator who wanted a reflection every three to four cycles has to remember to ask for it mid-flight, as 2026-10-06 nearly showed, when a plan spent its whole cap on fold-residue findings and a post-seal em-dash miss with no operator ask anywhere in the loop and nothing but the cap stood between that spend and a silent landing.

**After (this plan):** The same loop, three to four review-fix cycles in, pauses with the trajectory (staged counts, severities, and the new-root, fold-defect, wording split) and asks whether any scope extension is authorized before continuing. If new roots stop decreasing across two rounds, the same ask can fire before the cap. At the cap the loop stops with the three choices (cap closure, extend by N, park) and runs nothing until the operator answers; an unattended lane parks the plan and reports. Whichever way the loop ends, the terminal staging record carries the workflow-reflection paragraph: which defect classes the rounds staged, whether they converged, and which authoring-time or fold-time check would have front-loaded each.

Edge cases: a loop that certifies clean before the checkpoint never pauses (the duties are cap- and checkpoint-scoped, not unconditional); an operator choice to continue with cap closure runs today's closure shape byte-identically; a personal-class project keeps its three-round stop and simplify-or-rewrite escalation; an unattended lane never blocks waiting for an answer, it parks and reports.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three ask sites (checkpoint, non-convergence, cap boundary) and the reflection duty are each stated once in the prescribed prose, each with a dedicated validation span, and the cap-closure mechanics' bytes are untouched.
- regression safety: the pins suite passes; the em-dash touched scan and the public hygiene scan pass; the shared-body runtime-neutrality test passes over the edited plans skill.
- scope discipline: the changes touch only the two skills' round-lifecycle rules, the pins rows, and the validation block (the Integration Points duty is satisfied inside the same edits; the edits are in the two skills whose coupling the rounds already share, so no new integration lines are required beyond the pins' span coverage).

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- The next plan-review loop that reaches three to four cycles pauses with the reflection and scope-extension ask, a cap-boundary loop presents the three choices before any closure, and a terminal record carries the reflection paragraph; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (the cap-closure rule's opening and its byte-identical closing sentence, one checkpoint sentence beside the convergence-telemetry rule, and one reflection duty beside the round-close step; all other spans frozen)
- `agents/skills/review-plan/SKILL.md` (the Iteration Discipline cap-closure mirror's opening; all other spans frozen)
- `scripts/check_maintenance_pins.sh` (two pin rows beside the existing plans-skill pins)

**Tests:**
- none *(the machinery is prose; the mechanical witness is the pins rows and the span gates over existing suites)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-loop/SKILL.md`; reason: it owns the code-review loop, not the plan-review loop this origin targets (Assumptions above).
- `agents/skills/review-staging/SKILL.md` and `scripts/validate_review_staging.py`; reason: the `extensions.convergence` shape is defined in the plans skill's convergence-telemetry rule and carried by the sidecars; the plan renders it, never reshapes it.
- `scripts/plan_readiness.py`; reason: the reflection lives in the staging record, not the readiness gate, and no validator gate is added.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass`; the em-dash fixer reported 0 substitutions and the touched scan exited 0; the hygiene scan answered `OUTCOME: pass`; the shared-body forbidden-term precheck ran the prescribed insertion text against the gate's term tuple with zero hits; the rule 19 RED-today probes ran all six new-duty spans against the two skill files at the base tip with 0 matches each, and the two apostrophe-bearing pin spans were re-ground to apostrophe-free fragments before round 1 (rule 22's possessive rule); `bash -n` accepted the extracted Validation Commands block. Round-start state for r4 (post-reconciliation): the rule 13 reconciliation (docs/history/reviews/2026-10-07-plan-review-review-round-cap-operator-gate-reconciliation.md) replaced the hand-enumerated span gates with the list-driven loop and re-grounded the rule-16 span to its distinctive full form; the r4 round-start commit and digest are the reconciliation fold commit's. Round-start state for r1: authoring worktree ai-playbook-wt-rrc, branch 2026-10-07-review-round-cap-gate, base main b28c369c.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
span_fail=0
while IFS='|' read -r span_file span; do
  [ -n "${span:-}" ] || continue
  test "$(grep -cF "$span" "$REPO/$span_file")" -eq 1 || { echo "span not exactly once in $span_file: $span"; span_fail=1; }
done <<'SPANLIST'
agents/skills/plans/SKILL.md|stop and present the operator ask
agents/skills/plans/SKILL.md|pauses to present the concise convergence reflection
agents/skills/plans/SKILL.md|the checkpoint parks the plan and reports, never blocks waiting for an answer
agents/skills/plans/SKILL.md|may trigger the same ask before the cap
agents/skills/plans/SKILL.md|workflow-reflection paragraph
agents/skills/review-plan/SKILL.md|present the operator ask
agents/skills/plans/SKILL.md|the ask parks the plan and reports, never silently closes
agents/skills/plans/SKILL.md|run only on a recorded operator choice
agents/skills/plans/SKILL.md|the sidecar schema, and the personal-class limit are byte-identical on either choice
SPANLIST
[ "$span_fail" -eq 0 ] || exit 1
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k test_shared_skill_bodies_remain_runtime_neutral -q )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh touched )
( cd "$REPO" && bash "${PUBLIC_HYGIENE_SCAN:-$HOME/.ai-playbook/scripts/scan-public-hygiene.sh}" )
```

### Task 1: Pin the ask and reflection spans (RED probes)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (probe-only task)

Evidence:
- the span greps of `## Validation Commands` run against the current bytes; covers the RED-today criterion (every new-duty span absent before the edits)

- [x] Run → expect RED: every span in the Validation block's span list is absent from its target file before the edits (the loop names each), and the shared-body gate, pins suite, and scans pass unchanged [class: REPOSITORY_TEST]

### Task 2: Amend the plans skill's round lifecycle

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md` (three spans: the cap-closure rule's opening, the checkpoint sentence, the reflection duty)

Evidence:
- the span greps of `## Validation Commands`; covers the ask, checkpoint, reflection, park, and choice spans turning GREEN

- [x] Amend the cap-closure rule (rule 16) opening: before `close the loop through the cap-closure terminal shape instead of exceeding the cap or stranding the plan`, insert `stop and present the operator ask - the per-round trajectory (staged counts, severities, and the new-root, fold-defect, and wording split from the sidecars' extensions.convergence) with the three choices (continue with cap closure, extend by a stated number of rounds, or park the plan); in an unattended lane the ask parks the plan and reports, never silently closes - and run only on a recorded operator choice: ` so the rule reads as the ask preceding the closure; append to the rule's end: `The cap-closure terminal shape's mechanics, the sidecar schema, and the personal-class limit are byte-identical on either choice.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append one sentence to the convergence-telemetry rule (rule 12): `After three to four completed review-fix cycles without certification, the loop pauses to present the concise convergence reflection (the same trajectory data) and asks whether the operator authorizes any scope extension before continuing; in an unattended lane the checkpoint parks the plan and reports, never blocks waiting for an answer; new-root findings not decreasing across two consecutive rounds may trigger the same ask before the cap, and a generic continue answers only the presented question.` [class: IMPLEMENTATION_REQUIRED]
- [x] Append one sentence to the round-close step (rule 6's certification seal span): `The terminal round's staging record also carries the workflow-reflection paragraph: which defect classes the rounds staged (the extensions.convergence split), whether new roots converged round over round, and which authoring-time or fold-time check would have front-loaded each class.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the plans-side span checks of `## Validation Commands` [class: REPOSITORY_TEST]
- [x] Commit: `feat: operator checkpoints in the plan-review round lifecycle` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Mirror the cap ask in review-plan

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-plan/SKILL.md` (the Iteration Discipline rule 8 opening)

Evidence:
- the review-plan span check of `## Validation Commands`; covers the mirror ask span turning GREEN

- [x] Amend the Iteration Discipline rule 8 opening (the cap-closure procedure mirror): before `close it through the cap-closure terminal shape instead of exceeding the cap or stranding the plan`, insert `present the operator ask (the per-round trajectory from the sidecars' extensions.convergence with the three choices: continue with cap closure, extend by a stated number of rounds, or park; an unattended lane parks and reports) - closure runs only on the operator's recorded choice: ` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the review-plan span check of `## Validation Commands` [class: REPOSITORY_TEST]
- [x] Commit: `feat: mirror the cap-boundary operator ask in review-plan` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Pins rows and full validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh` (two pin rows beside the existing plans-skill pins)

Evidence:
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins criterion with the two new rows green
- the shared-body gate line of `## Validation Commands`; covers the forbidden-term criterion over the edited plans skill

- [x] Append two pin rows beside the existing plans-skill pins (the `$PL` block): `pin "plans cap-boundary operator ask present" grep -qF 'stop and present the operator ask' "$PL"` and `pin "review-plan cap-boundary operator ask present" grep -qF 'present the operator ask' "$repo/agents/skills/review-plan/SKILL.md"` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the complete `## Validation Commands` block → expect exit 0 on the executed tree [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the operator checkpoint spans` [class: IMPLEMENTATION_REQUIRED]
