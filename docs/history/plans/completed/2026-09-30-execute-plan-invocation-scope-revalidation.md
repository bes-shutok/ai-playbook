# Plan: Execute-plan invocation scope revalidation

Backlog origin: docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-execute-plan-invocation-scope-revalidation-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Execute-plan's invocation detection reclassifies every new user message on its own content before a prior gate choice can authorize execution, so a carried execute choice can no longer start implementation for a request that switched to authoring, review, or merge work.

- A prior execute-plan gate choice stays bound to the plan run it authorized; a message about a different objective (authoring, reviewing, updating, summarizing, branch cleanup, landing or merging a branch, or any other plan management) classifies as not invoked even when it references the same plan.
- Automatic continuation inside one explicitly selected plan run is preserved: an explicit same-plan execution request resumes without re-showing the gate.
- A regression pin suite keeps the reclassification contract mechanically observable, so future wording drift in the invocation section fails a test instead of silently widening the carried choice's scope.

Gate delta: one checked-condition set is added to the existing invocation-classification refusal surface (signal E grows a plan-identity and objective binding, and a new reclassification duty is inserted between detection and the plan-path gate). This is a refusal-path addition on a fix-class origin; the three class-default exits are impossible per the origin body: removing the gate signal entirely (dropping signal E) is the origin's rejected alternative "remove prior-choice continuation entirely" because it reintroduces repeated execute-plan gates between steps of one active run; there is no false positive to remove because the false positive is the signal's unbounded scope itself, and the origin's rejected alternative "carry execution intent across unrelated objectives until the session ends" is precisely the witnessed defect; the origin's remaining rejected alternative, "treat phrases such as 'finish the plan' as execution by default", is impossible because such phrases do not distinguish finishing plan authoring from executing its tasks, which is why this plan's explicit-resume arm keys on the invocation signals (A, B, or C) rather than phrase defaults; narrowing the carried choice's scope (the shape this plan takes) is the sanctioned exit the origin's Fix shape prescribes.

## Terms

- **Invocation detection**: the run-first classification in `agents/skills/execute-plan/SKILL.md` that decides `invoked = true/false` from signals A through E.
- **Carried choice (prior gate choice)**: the signal E record that the user selected execute-plan (option 1) at the plan-path gate earlier in the same session.
- **Plan run**: one explicitly selected execute-plan invocation for one plan path, from selection through archive; the unit a carried choice is bound to.
- **Objective switch**: a user message whose current request is plan authoring, updating, reviewing, summarizing, branch cleanup, landing, merging, or any other plan management rather than executing that plan's tasks.
- **Reclassification**: the duty to classify each new user message by its own content first and let a clear objective switch supersede the carried choice.

## Assumptions

- assume the fix is a behavioral contract amendment to `agents/skills/execute-plan/SKILL.md` (prose + worked examples + an anti-pattern row) enforced by a new mechanical pin suite, not a runtime-code change; basis: the origin item's Issue archaeology and Fix shape locate the defect in the skill's invocation detection prose (signal E, introduced in commit 02348755), and invocation detection runs agent-side before any runtime driver exists.
- assume the origin item's Fix shape is the confirmed design (bind the carried choice to plan identity and active execution objective; reclassify every message; supersede on objective switch unless the message explicitly resumes execution; keep commit, merge, and push authorization under their own rules); basis: the origin item records the user's interactive correction of 2026-09-29 with rejected alternatives, and the standing operator directive of 2026-09-30 directs authoring the most urgent backlog items in cycles without interruption.
- assume the origin item's classification is fix-class (a defect removal, not machinery growth) judged from its body; basis: no `Class:` header line is present; the body records a witnessed unauthorized-implementation incident (implement worker and runtime claim started without current authorization) and prescribes a narrowing remedy.
- assume the repository's pytest-runner contract applies to the new suite (venv interpreter first, ambient pytest fallback with a version guard); basis: plan `docs/history/plans/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation) records this exact runner contract because ambient python3 carries no pytest.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: execute-plan's prior-choice signal is scoped to one plan run and one objective, so a stale execute choice can no longer authorize implementation after the user switches goals; the driving force is code-quality (authorization correctness).

Before (today): the user picks execute-plan (option 1) at the plan-path gate for plan X. Later in the same session the user says "finish and merge the plan-authoring branch". Signal E matches (a prior gate choice exists in this session), `invoked = true`, the gate is skipped, and the session interprets the message as execution: an implement worker and a runtime claim start for work the user did not authorize. This is the witnessed 2026-09-29 incident recorded in the origin item.

After (this plan): the same later message is classified by its own content first. Its content is a landing/merge request, an objective switch; the carried choice is superseded and `invoked = false` for that message, so the requested flow (merge management, or the plan-path gate) governs. When the user instead says "continue the plan" for the same plan X, the explicit execution signal in the message resumes the same plan run without re-showing the gate, preserving today's no-repeated-prompts behavior inside one run.

Concrete examples the amended section pins:

| Prior choice | New message | `invoked` | Action |
|---|---|---|---|
| execute chosen for plan X | "now finish and merge the authoring branch" | false | Objective switch; requested flow governs; no execution starts |
| execute chosen for plan X | "continue the plan" | true | Same plan run resumes; no re-gate |
| execute chosen for plan X | "review this plan" | false | Review flow; not execution |
| execute chosen for plan X | "execute plan docs/history/plans/Y.md" (different plan Y) | true | Fresh invocation signal for plan Y; the new plan run starts under its own selection |

## Evaluation Criteria

**Quality dimensions:**
- correctness: every objective-switch message classifies as not invoked solely from signal E; every explicit same-plan resume classifies as invoked without a re-gate; the pin suite asserts both directions mechanically.
- regression safety: signals A through D are unchanged, and the pin suite carries a characterization test asserting the current A-D signal-row anchor spans so that unchanged claim is mechanically observed; a plan run's internal step continuation still never re-shows the gate.
- maintainability: the contract is pinned by a dedicated unittest file so wording drift fails a named test; the shared-body runtime-neutrality gate still passes over the amended shared skill body.

**Done when:**
- `agents/skills/execute-plan/SKILL.md` carries the bound signal E wording, the reclassification subsection, the two-side worked examples, and the anti-pattern row.
- `scripts/test_execute_plan_invocation_scope.py` passes; the RED-today evidence (failure before the SKILL.md amendment) is recorded in the plan's task log.
- All Validation Commands exit 0 from the worktree root.

**Ship when:**
- Consumer runtimes pick up the amended skill through the operators' normal vendored-asset sync; no further release action is required by this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`

**Tests:**
- `scripts/test_execute_plan_invocation_scope.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/runtime-contract.md` and `scripts/execute_plan_runtime.py`; reason: the defect lives in agent-side invocation classification before the runtime driver participates; runtime claim behavior is the witnessed consequence, not the fix surface.
- Other skills' SKILL.md files; reason: only execute-plan carries the signal E prior-choice mechanism.

## Validation Commands

```bash
# Runner contract: venv pytest interpreter first, ambient fallback with a loud guard.
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The reclassification pin suite passes.
"$TEST_PY" -m pytest scripts/test_execute_plan_invocation_scope.py -q || { echo "FAIL: invocation scope pins" >&2; exit 1; }

# 2. The shared-body runtime-neutrality gate still passes over the amended skill body.
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q || { echo "FAIL: shared-body neutrality" >&2; exit 1; }

# 3. Signal E carries the plan-run and objective binding (fixed-string pin, distinct span).
grep -qF 'User already chose execute-plan (option 1) earlier in this session for the current plan run' agents/skills/execute-plan/SKILL.md || { echo "FAIL: signal E binding missing" >&2; exit 1; }

# 4. The reclassification subsection exists with its four contract spans (per-span dedicated pins).
grep -qF '### Choice scope and reclassification (prior-choice signal E)' agents/skills/execute-plan/SKILL.md || { echo "FAIL: reclassification heading missing" >&2; exit 1; }
grep -qF 'classify the new message by its own content first' agents/skills/execute-plan/SKILL.md || { echo "FAIL: own-content-first duty missing" >&2; exit 1; }
grep -qF 'an objective switch supersedes the carried choice' agents/skills/execute-plan/SKILL.md || { echo "FAIL: supersession duty missing" >&2; exit 1; }
grep -qF 'resumes the same plan run without re-showing the gate' agents/skills/execute-plan/SKILL.md || { echo "FAIL: explicit-resume arm missing" >&2; exit 1; }

# 5. The worked examples pin both directions (author-and-merge false; same-plan resume true).
grep -qF '| execute chosen for plan X | "now finish and merge the authoring branch" | false |' agents/skills/execute-plan/SKILL.md || { echo "FAIL: objective-switch example missing" >&2; exit 1; }
grep -qF '| execute chosen for plan X | "continue the plan" | true |' agents/skills/execute-plan/SKILL.md || { echo "FAIL: same-plan resume example missing" >&2; exit 1; }

# 6. The anti-pattern row names the witnessed defect class.
grep -qF 'Carry a prior execute choice into a materially different authoring or merge request' agents/skills/execute-plan/SKILL.md || { echo "FAIL: anti-pattern row missing" >&2; exit 1; }

# 7. Em-dash gate over the branch's added lines (added-lines mode requires an explicit base).
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): pre-round structural gate (`plan_readiness --pre-round`), the em-dash `touched` scan, and the public-hygiene scan ran over these plan bytes before round 1 and passed (the pre-round run caught a missing classification tag on three Commit items, folded before round 1). RED-today evidence, rule 19: the SKILL.md pin commands (Validation Commands 3 through 6) were executed against the unamended tree and every pinned span is absent, so each grep fails as required; commands 1 and 2 could not run at authoring time because the pin suite file does not exist yet (it is Task 1's deliverable), and Task 1's Run-expect line owns their RED verification at execution. Rule 22 mechanical audit: each pinned span occurs exactly twice in this plan (its Validation Command grep plus its Task prescription), and `bash -n` over this block passed.

### Task 1: Pin the reclassification contract (RED)

Files:
- `scripts/test_execute_plan_invocation_scope.py` *(new)*

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_execute_plan_invocation_scope.py -q`; covers: the pin suite exists, is collectable, and fails against the unamended SKILL.md.

- [ ] Create `scripts/test_execute_plan_invocation_scope.py` as a `unittest.TestCase` suite that reads `agents/skills/execute-plan/SKILL.md` relative to the repo root and asserts, as separate test methods with fixed-string spans, each Validation Command pin above: the bound signal E row, the reclassification heading, the own-content-first duty, the supersession duty, the explicit-resume arm, the two worked-example rows, and the anti-pattern row. [class: REPOSITORY_TEST]
- [ ] Add one further separate test method (characterization, GREEN by construction today) asserting the current signal A-D row anchor spans are present, for example the signal A match-cell text `Message contains `execute plan``, the signal C cell `contains `execute-plan` or `/execute-plan``, and the signal D row `This `execute-plan` skill is attached`; this is the regression witness for the Evaluation Criteria claim that signals A through D stay unchanged. [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$TEST_PY" -m pytest scripts/test_execute_plan_invocation_scope.py -q` exits non-zero with the new-span pin tests failing (the spans are absent from the unamended SKILL.md); the A-D characterization test passes by construction because it pins today's rows. [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin execute-plan invocation scope reclassification contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Bind signal E and add the reclassification duty (GREEN)

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `"$TEST_PY" -m pytest scripts/test_execute_plan_invocation_scope.py -q`; covers: every contract pin passes against the amended section, and the shared-body neutrality gate still passes.

- [ ] In the Invocation detection signal table, replace the signal E "How to match" cell so it reads: `User already chose execute-plan (option 1) earlier in this session for the current plan run, and the current message does not switch objective (see Choice scope and reclassification)`; keep the signal table's shape otherwise unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert a subsection `### Choice scope and reclassification (prior-choice signal E)` immediately after the Algorithm subsection's plan-path heuristic paragraph, prescribing: the carried choice is bound to one plan run (the plan path the gate option selected) and to an active execution objective for it; classify the new message by its own content first (signals A through D); when the message concerns the same plan run and does not switch objective, signal E keeps `invoked = true` so steps inside the run never re-show the gate; an objective switch supersedes the carried choice, so `invoked = false` for that message and the requested flow (authoring, review, update, summarizing, branch cleanup, landing or merge management, or any other plan management) or the plan-path gate governs, even when the message references the same plan; a current-message execution signal (A, B, or C) that names the same plan resumes the same plan run without re-showing the gate, and one naming a different plan starts a fresh selection for that plan; the carried choice never authorizes commits, merges, or pushes for the superseding objective, which stay governed by their own rules. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add to the worked-examples table the two-side rows exactly as pinned in Validation Commands 5 (objective switch false; same-plan resume true), plus the review-request row and the different-plan row from the Gist table. The target shape is explicit: extend the worked-examples table with a leading Prior choice column (the existing rows gain an `n/a` cell in that column and their rows keep their three existing cells), then append the four Gist rows under the extended four-column header. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the third bullet of the "Execute-plan already chosen (skip gate; proceed immediately)" list, which restates signal E, to carry the binding: `Prior gate choice for the current plan run and objective (see table E and Choice scope and reclassification)`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add one anti-pattern row: `Carry a prior execute choice into a materially different authoring or merge request` with the why-column explaining the binding and naming the witnessed 2026-09-29 stale-choice implementation start. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$TEST_PY" -m pytest scripts/test_execute_plan_invocation_scope.py -q` exits 0, and `"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: bind execute-plan prior-choice signal to plan run and objective` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Whole-plan validation gate

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- The full `## Validation Commands` block run from the worktree root; covers: every criterion in Done when.

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0 with its failure branch armed (a deliberately broken pin check in a scratch copy of the test file exits non-zero before the real run). [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for invocation scope revalidation` [class: REPOSITORY_TEST]

## Superseded disposition (2026-09-30)

Archived as superseded without execution: a parallel authoring session executed its own plan for the same origin (docs/history/backlog/2026-09-29-execute-plan-prior-invocation-scope-leak.md, marked done via docs/history/plans/completed/2026-09-30-execute-plan-prior-choice-scope-binding.md, exec r1 zero blocking), landing an equivalent invocation-scope contract on main (signal E bound to the plan in play plus a reclassification precedence paragraph, main 0f4b7cf5/f97277f9). This plan's pinned spans are absent from the live SKILL.md by design of that landing; executing this plan would rewrite the executed implementation's wording. The r1/r2 review record (docs/reviews/2026-09-30-plan-review-execute-plan-invocation-scope-revalidation-r1/r2) stays as history; this plan's r2 certification (ready=yes, zero blocking, digest c57e3430) attests only its own bytes.
