# Plan: done's plan-readiness result becomes advisory with candidate retirement

Backlog origins (scope of record):
- docs/history/backlog/2026-10-06-done-unrelated-gate-blocks-closeout.md
- docs/history/backlog/2026-10-05-authoring-certification-staging-series-gate.md

Driving force: reliability
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-done-readiness-closeout-boundary-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-06-done-readiness-closeout-boundary.md (session sess_1e13991c-8e25-4535-9a7e-ae31500fc603)

## Terms

- plan-readiness gate: the done pre-docs sweep gate `gate_plan_readiness` in `scripts/done_sweep_gates_lib.py`, which runs each session candidate through `scripts/plan_readiness.py` as a CLI child and buckets the child's four-outcome result.
- modeled ready=no: a child result of `OUTCOME: fail` with exit 1, the validator's own verdict that a gated plan's latest review does not cover its current bytes.
- advisory result: a gate finding reported in the gate's message while the gate exits 0, so the closeout proceeds after the result is durably reported.
- candidate retirement: pruning the candidate's line from the deliverables queue after its result is durably reported, so a later closeout does not reconsider it.
- certification claim: the authoring run's acceptance that its plan is reviewed and certified, witnessed by the certification seal the round-close step writes.
- the blueprint: the authoring task payload in `agents/skills/maintenance/prompt-templates.md` (the `Schedule at {schedule_time}` task paragraph).
- recorded-stop: the done skill's only sanctioned way past a blocking gate failure, an explicit operator choice recorded in the session log.
- staging records: the per-round review-record pair under the reviews home (the Markdown record and its `.stats.json` sidecar).
- deployment-gap: the validator-or-tooling-missing failure class the done plan-readiness bullet defines, never remedied by recorded-stop.

Configuration (from facts document): none required; the Validation Commands resolve the test interpreter inline with the landed fallback precedent (the venv interpreter when present, else the system python3, whose missing pytest fails loudly as a configuration gap, never a test failure).

## Why

A done closeout could not commit this session because a plan's independent review was still pending: the plan-readiness gate reported a modeled ready=no and blocked, coupling the closeout to work outside its scope. The sibling defect is the sequencing twin: the authoring blueprint records its certification claim before the authoritative gate has run over the assembled staging series, so staging defects surface at landing time where they cost the most.

## Outcome

A modeled ready=no is reported and retired instead of blocking the closeout, and the authoring blueprint runs the authoritative gate over the assembled series before the run's landing acceptance.

- An unrelated done run completes its own commit work while the pending plan is reported as a draft or pending review, never execution-ready.
- A later closeout does not reconsider a retired candidate; the plan artifact and its independent review state stay exactly where the plans and execute-plan workflows enforce them.
- A staging-record defect found by the full gate is corrected and the gate re-run before the run's landing acceptance, without launching another review round.

Gate delta: no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed; the plan-readiness gate's modeled-fail arm narrows from blocking to advisory-with-retirement, the exit the fence-class origin prices (cited: docs/history/backlog/2026-10-06-done-unrelated-gate-blocks-closeout.md, the witnessed closeout block and the operator's clarification), and the blueprint's certification duty gains the full-gate-before-acceptance sequencing the fix-class origin prices (cited: docs/history/backlog/2026-10-05-authoring-certification-staging-series-gate.md, three witnessed late-gate failures); the indeterminate, tool-error, recorded-stop, and deployment-gap arms keep their current bytes, and execute-plan's pre-implementation readiness refusal is untouched.

## Assumptions

- assume the done sweep suite runs through the facts-resolved test interpreter (Configuration above); basis: the suite uses pytest fixtures and the system python3 lacks pytest, while the suite ran green through the venv interpreter at main `716ac879` on 2026-10-07 (184 passed, 3 subtests, 18.12s); if execution observes a different count, the re-pin is a plan correction and the pinned numbers are never edited to chase the count.
- assume retiring a modeled-fail candidate is safe because the prune already covers the passed, exempted, and archived buckets the same way; basis: the same `_prune_deliverables` call and the origin's expected behavior ("report unrelated pending work separately without making it a prerequisite to commit"), and the recorded-stop arm already prescribes removing the excluded path's lines from the same queue; the two tests pinning the removed behavior are updated in the same task.
- assume the certification-ordering obligation is enforced at the post-loop acceptance boundary (the run's done processing and landing acceptance) rather than before the seal; basis: the certification claim's witness (the seal) is written by the review round's round-close step inside the loop, so a blueprint-level gate cannot precede it; this records the divergence from the entry's before-the-claim wording, resolving in the strongest direction the insertion position can enforce, with the fail arm ending the run explicitly uncertified (no landing, no done processing of the plan as ready) and an already-recorded seal governed by the review-staging validator's seal-freshness and corrections arms.
- assume no maintenance-pin row names a span this plan edits; basis: a grep over `scripts/check_maintenance_pins.sh` for the gate message, the done bullet's replaced span, and the blueprint sentence shows no intersecting literal, and rule 41's pin sweep re-runs at every fold.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: done's plan-readiness verdict is reported and retired instead of blocking the closeout, and the authoring blueprint runs the authoritative gate before the run's landing acceptance (reliability).

**Before (today):** a modeled ready=no exits the plan-readiness gate at 1 and blocks the done closeout, and the failed candidate's deliverable line stays queued so a later closeout re-blocks; the authoring blueprint accepts a ready=yes review and records its certification claim before the full gate has ever run over the assembled staging series.

**After (this plan):** the same verdict is reported in the gate's message with the candidate retired from the queue, the gate exits 0, and the closeout proceeds with the plan described as a draft or pending review; the blueprint runs the full gate over the assembled series before its landing acceptance, correcting staging records on a fail without launching another review round.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a modeled ready=no candidate is reported (gate exit 0, the failure named in the message) while its deliverable line is pruned; indeterminate and tool-error children still land in their blocking buckets; an owned closeout integrity failure still blocks.
- regression safety: the full done sweep suite passes with one added test and two existing tests updated to the advisory contract; the maintenance pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: only the four listed files change; execute-plan's pre-implementation readiness refusal and the validator itself are untouched.

**Done when:**
- `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -q` passes at 185 tests (the 184 pre-existing, two of them updated to the advisory contract, plus the new advisory test), with the subtests passing.
- Every span check in `## Validation Commands` holds on the executed tree.

**Ship when:**
- The next done closeout carrying a pending-review plan commits the session's authorized work while reporting the plan as pending, and the next authoring run's landing acceptance follows a passing full-gate run; they follow from the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the `gate_plan_readiness` failed bucket and its docstring; all other gates frozen)
- `agents/skills/done/SKILL.md` (the plan-readiness bullet in the gates list)
- `agents/skills/maintenance/prompt-templates.md` (the blueprint's certification sentence)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (the new advisory-path test; two existing tests updated to the advisory contract, the other 182 frozen)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and the review-staging validator: reason: the entry keeps both as the untouched authorities; the plan changes only how their verdicts are consumed.
- `agents/skills/execute-plan/SKILL.md` Phase 0: reason: an unready plan stays ineligible for execution, the refusal this plan explicitly preserves.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target after the r1 fold (the new-duty spans returned no match: the advisory docstring sentence and the amended dominance comment 0 each in the gate file, the done bullet's advisory clause 0, and the blueprint sequencing span 0; the replaced spans matched at 1 today, headed to their post-edit values: the done bullet's refusal span to 0, the blueprint anchor span to the sequenced form); the preserved spans matched: the recorded-stop sentence and the blueprint certification sentence at 1 each; the rule 22 mechanical audit verified every pinned span occurs in its owning prescribed snippet (rule 36 mirrors included) and `bash -n` accepted the Validation Commands block including the inline interpreter resolution; the em-dash touched scan and the hygiene scan both exited 0. Round-start state for r2: authoring worktree ai-playbook-wt-drcb, branch 2026-10-06-done-readiness-closeout-boundary, plan bytes at the post-fold commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
[ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
( cd "$REPO" && test -f scripts/done_sweep_gates_lib.py )
( cd "$REPO" && "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q )
( cd "$REPO" && test "$(grep -cF 'modeled ready=no result is advisory' scripts/done_sweep_gates_lib.py)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'a modeled fail is advisory with its candidate retired' scripts/done_sweep_gates_lib.py)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'test_plan_readiness_modeled_fail_is_advisory' scripts/test_done_sweep_gates_lib.py)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'refuse to finalize; require a fresh' agents/skills/done/SKILL.md)" -eq 0 )
( cd "$REPO" && test "$(grep -cF 'is advisory to this closeout' agents/skills/done/SKILL.md)" -eq 1 )
( cd "$REPO" && test "$(grep -cF 'the ready state carrying the assembled-series full-gate duty' agents/skills/maintenance/prompt-templates.md)" -eq 1 )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)" )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: the modeled ready=no becomes advisory with candidate retirement

Context surface: the plan's Terms and this task.

Files:
- `scripts/done_sweep_gates_lib.py` (the `gate_plan_readiness` function)
- `agents/skills/done/SKILL.md` (the plan-readiness bullet)
- `scripts/test_done_sweep_gates_lib.py` (one new test)

Evidence:
- `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the advisory criterion: the new advisory test passes, the two updated tests assert the advisory contract, and the other 182 pre-existing tests stay green
- the span checks in `## Validation Commands`; covers the wording criterion: the refusal clause gone from the done bullet, the advisory clause present exactly once, the advisory mechanism present in the gate

- [x] In `scripts/done_sweep_gates_lib.py`, in `gate_plan_readiness`: extend the post-loop retirement set so failed candidates retire with the passed ones (the line `remove.update(passed)` gains a sibling line `remove.update(str(plan) for plan, _ in failed)`), and change the failed bucket from blocking to advisory: delete the arm guarded by `if failed:` whose body is the single line `return GateResult(gate, 1, message, warnings=[])` so the function falls through to the passing return while the message keeps naming `failed=N` and the first failures (the indeterminate and tool-error arms above it keep their current bytes); amend the two dominance clauses that the advisory arm falsifies, located inside `gate_plan_readiness` and named descriptively because both are line-wrapped in the source: the docstring's dominance lead-in and parenthetical (from `The aggregate exit carries the dominant bucket` through the parenthetical ending \`\`phase_exit\`\`)) is rewritten as the single line `The aggregate exit carries the dominant bucket (tool error dominates indeterminate, matching \`\`phase_exit\`\`; a modeled fail no longer carries the aggregate exit, the advisory arm above)`, the sentence's trailing message-naming clause (`while the message names every non-passing bucket (the contract's multi-input rule)`) surviving byte-identical, and the tool-error arm's comment (the comment line naming the dominance order, sitting above the deleted arm's position) is rewritten as the single line `# Tool error dominates indeterminate for the same run, and a modeled fail is advisory with its candidate retired`; and extend the function docstring's outcome description with one sentence naming the modeled ready=no result advisory (`A modeled ready=no result is advisory: reported with its first failure, its candidate retired, the closeout proceeding.`) [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/done/SKILL.md`, in the plan-readiness bullet, replace the span `refuse to finalize; require a fresh \`review-plan\` round (after any plan edit that changes the digest) before re-running the gate, except when` with `a modeled \`OUTCOME: fail\` (the validator's ready=no) is advisory to this closeout: the runner reports the candidate and its first failure line, prunes its deliverable line so a later closeout does not reconsider it, and proceeds, describing the plan as a draft or pending review, never execution-ready, while its independent review state stays enforced by the plans and execute-plan workflows; a fresh \`review-plan\` round (after any plan edit that changes the digest) is still what makes that plan execution-ready anywhere, except when`, keeping the rest of the bullet byte-identical including the recorded-stop and deployment-gap arms [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/test_done_sweep_gates_lib.py`, update the two tests that pin the removed blocking behavior to the advisory contract: `test_deliverables_removal_rule` now asserts the gate exit code 0 with `failed=1` and the stub's first failure line in the message and the failed candidate's line pruned from the queue alongside the other buckets, and `test_report_shape_and_order` now asserts the pre-docs phase and its plan-readiness row exit code 0 in that all-green fixture; the other 182 tests keep their bytes [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/test_done_sweep_gates_lib.py`, add `test_plan_readiness_modeled_fail_is_advisory` beside the existing child-outcome tests (mirroring their stub-validator fixture pattern): the stub validator prints `OUTCOME: fail` and exits 1, the gate returns exit code 0 with `failed=1` and the stub's first failure line in its message, and the candidate's deliverable line is absent from the queue after the call [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `$TEST_PY -m pytest scripts/test_done_sweep_gates_lib.py -q` passes at 185 tests (184 pre-existing plus the new one) with the subtests passing; the advisory and done-bullet span checks read as pinned [class: REPOSITORY_TEST]
- [x] Commit: `feat: done's plan-readiness verdict is advisory with candidate retirement` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the blueprint's full gate runs before the run's landing acceptance

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/maintenance/prompt-templates.md` (the blueprint's certification sentence)

Evidence:
- the span check in `## Validation Commands`; covers the sequencing criterion: the blueprint's certification sentence carries the full-gate-before-acceptance obligation exactly once

- [x] In `agents/skills/maintenance/prompt-templates.md`, in the blueprint's certification sentence, replace the span `the ready state carrying the certification-ordering duty (before it is treated as reached, run the readiness validator's full gate over the final plan bytes and require its final \`OUTCOME: pass\` line, repairing any staging-record defect record-side and re-running the gate before proceeding, so the authoritative gate never first runs at landing time)` with `the ready state carrying the assembled-series full-gate duty (after the final round's staging records are assembled, run the full readiness gate (python3 scripts/plan_readiness.py <plan-path>) over the assembled series and record its outcome beside the run's certification evidence; the done processing and the landing acceptance of this run proceed only on exit 0 with the final \`OUTCOME: pass\` line; on a gate fail, correct the staging records (schema fields, digest format, record-surface agreement, verdict line) and re-run the gate, a gate failing late never launching another review round, and a run whose gate still fails ends with the plan explicitly uncertified (no landing, no done processing of the plan as ready; an already-recorded seal is governed by the review-staging validator's seal-freshness and corrections arms))`, keeping both neighboring spans byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the blueprint span check reads exactly 1; the done sweep suite still passes (no code changed in this task) [class: REPOSITORY_TEST]
- [x] Commit: `feat: the authoring blueprint runs its full gate before landing acceptance` [class: IMPLEMENTATION_REQUIRED]

## Amendment record (mid-execution, shared-file seam)

Amended 2026-10-07 before execution, per arm (a) of docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md: the sibling plan authoring-staging-preflight-gates executed first (main 654560dc) and landed the certification-ordering form over the payload span this plan's Task 2 originally anchored on (`record the residual findings in the plan), and the workflow is processed`), so this plan's Task 2 prescription re-anchors on the landed form and delivers its assembled-series duty as the replacement. The duty content is unchanged: the full gate runs over the final bytes before the ready state is treated as reached; this plan's form adds the assembled-series object and the outcome-record beside the certification evidence. The Validation Commands span check re-keys to the amended prescription's anchor.

Execution correction 2026-10-07 (adopting session): the done sweep suite observes 189 tests (not the pinned 185) at Task 1 verification; per the Assumptions interpreter-count rule the pinned numbers are not edited; the delta is four tests that predate this run on the branch base (654560dc lineage).
