# Plan: churn-trigger degraded-round comparability

Backlog origin: docs/history/backlog/2026-11-07-churn-trigger-degraded-round-comparability.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-08-plan-review-churn-trigger-degraded-round-comparability-pc53a5807-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h
Executed: yes (93385f2f987d6d82f774c6870872d98df9ebd5e4)
Authoring claim: churn-trigger-degraded-round-comparability.md (session sess_5fd706c9-4024-41e8-8071-8cbef294ceda)

## Terms

- comparable round: a review round whose staging sidecar coverage outcome is neither `degraded` nor `failed` and whose panel carries no row whose status is anything other than `complete`.
- coverage-degraded round: any round that is not a comparable round: its coverage outcome is `degraded` or `failed`, or at least one panel row was skipped, failed, or timed out.
- comparison window: the two rounds a churn-trigger sentence compares.
- churn trigger: review-plan's measured non-convergence trigger over staged-findings and open-blocking totals.
- baseline round: the first comparable round a continuing loop establishes when fewer than two comparable rounds exist.
- round record: the staged review Markdown and its `.stats.json` sidecar pair for one round.

## Why

The churn triggers compare the two most recent rounds' totals. A coverage-degraded round contributes totals from a fraction of the panel, so the literal comparison both under- and over-fires: in the witnessed run the degraded r2 (1 of 5 workers, 4 staged) against the full r3 (13 staged) read as "not decreasing", and the orchestrator had to improvise an exclusion argument inside one round record to proceed without operator direction.

## Gist & Examples

TLDR: the review-plan churn trigger's comparison window runs over comparable rounds only, excluding coverage-degraded rounds with a fewer-than-two-baseline arm and a recorded exclusion line, mirrored into review-reconciliation's trigger audit, because a degraded round's partial totals are not trajectory points.

After this plan, a loop whose adjacent round timed out half its panel no longer fires the non-convergence machinery on the literal totals: the comparison runs over the most recent comparable rounds, and a loop with only one comparable round so far continues one round to establish the baseline instead of pausing for operator direction. The witnessed true-positive firing across two full-panel rounds (staged 13 to 13 and blocking 3 to 5 by the round sidecars' counts; the witnessed firing statement counted the round's one overflow row as the 14th) still fires: both rounds are comparable, so the clause never suppresses it, and neither total decreases.

## Outcome

The non-convergence machinery fires only on rounds that are actually comparable, ending both the spurious-fire exposure and the per-round improvised exclusion arguments.

- A coverage-degraded round adjacent to full rounds no longer makes the churn trigger fire on partial totals.
- A loop with fewer than two comparable rounds continues one round instead of firing.
- Each excluded round leaves one recorded line, so the reconciliation pass can audit the exclusion.
- review-reconciliation audits a firing over comparable rounds the same way when it is invoked.

Gate delta: prose-only amendments to three skill files (one added comparability definition plus window wording changes; review-loop's duplicated inline trigger restatement is deleted in favor of a pointer to the owned definition); no gate, validator, lock, ledger, required ceremony, or schema field added; the exclusion record is one prose line in the round record, deliberately not a new `extensions.convergence` schema member (rejected: a schema member is a counted-class addition the origin's machinery-admission paragraph excludes, and the five-counter plus `self_heal_attempt` shape is validator-owned); the review-loop deletion pays the added definition sentence; witnessed incident: the degraded-r2-versus-full-r3 pair recorded in the origin row.

## Assumptions

- assume a comparable round requires `complete` status on every panel row; basis: the witnessed degraded round r2's sidecar shows coverage outcome `degraded` with one panel row complete and the other four timed-out, failed, or skipped, so both arms (coverage outcome, panel-row status) name the same witnessed round and the two-arm definition catches skips that leave coverage outcome untouched.
- assume the exclusion record is one prose line in the round record, not a new `extensions.convergence` member; basis: the origin's machinery-admission paragraph excludes schema additions, and the convergence shape (five classification counters plus `self_heal_attempt`) is validator-owned; the reconciliation pass reads the chronological round records, so a recorded line is auditable without schema change.
- assume the witnessed r4 true-positive firing over two full-panel rounds still fires under the amended text; basis: both rounds are comparable (all workers completed, coverage clean), so the comparison window is unchanged for it; verified against the amended sentence at authoring time.
- assume review-loop needs the clause too; basis: review-loop's orchestration rule 5 restates the measured churn trigger's totals comparison inline (verified against its text), so excluding it would leave a divergent operative definition firing literally on degraded rounds; execute-plan's triggers are recurrence-group based and its continuation policy resolves through review-plan's text, so execute-plan stays excluded.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: review-plan carries the two-arm comparable-round definition (one definition, no duplicate copy), review-reconciliation's audit bullet runs the window over comparable rounds using that definition, review-loop's rule-5 firing resolves through the owned definition instead of its inline restatement, and the fewer-than-two arm routes to continue-one-round rather than firing.
- growth balance: the clause lands inside the existing sentences (window wording changes) plus one added definition sentence and one Trigger bullet, with no incident narrative in skill text; the origin row stays the dossier.
- compatibility: no validator, schema, or gate change; the existing record-validation battery stays green.

**Done when:**
- Both amended files carry the clause with the two-arm comparable-round definition, and a grep for `comparable round` finds the definition in review-plan and the audit bullet in review-reconciliation.
- The em-dash, hygiene, instruction-size, and description-length gates pass on the changed files.
- The witnessed degraded-r2-versus-full-r3 pair no longer fires under the amended sentence (authoring-time check recorded in the review record), and the full-panel r4 pair still fires.

**Ship when:**
- None beyond the repository changes; the clause takes effect at landing.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-plan/SKILL.md` (Task 1)
- `agents/skills/review-reconciliation/SKILL.md` (Task 2)
- `agents/skills/review-loop/SKILL.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; reason: its continuation policy resolves through review-plan's text and its own triggers are recurrence-group based, not totals comparisons (verified at authoring).
- `scripts/validate_review_staging.py`, `scripts/review_record_selection.py`; reason: no schema or tooling change; the exclusion record is round-record prose.
- `.stats.json` sidecar shape; reason: deliberately unchanged (see Gate delta).

## Validation Commands

```bash
grep -c "comparable round" agents/skills/review-plan/SKILL.md
grep -c "comparable round" agents/skills/review-reconciliation/SKILL.md
bash scripts/check-no-em-dash.sh file agents/skills/review-plan/SKILL.md
bash scripts/check-no-em-dash.sh file agents/skills/review-reconciliation/SKILL.md
bash scripts/check-no-em-dash.sh file agents/skills/review-loop/SKILL.md
if grep -q "two most recent rounds" agents/skills/review-loop/SKILL.md; then echo "FAIL: review-loop still restates the churn trigger totals comparison"; exit 1; fi
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

Validation preamble (authoring-time preflight record, 2026-11-15): the em-dash `file` scans pass on all three target files; the public hygiene scan reports `OUTCOME: pass`; `grep -c "comparable round"` returns 0 on review-plan and review-reconciliation today (the definition lands with Tasks 1 and 2); the forbidden-sweep target phrase occurs exactly once in review-loop today (RED-today per rule 19, simulated rewritten sweep exits 1 with the FAIL line), flipping GREEN when Task 3 lands; the structural-only pre-round gate passes (`OUTCOME: pass`, 2026-11-15, over the post-r1-fold bytes). Round-start state for r2: commit 39a52e94f10d6458d90fbf713b777d2db5396a8f, plan digest 28a8c30fa3812497ee9f305e3f11b0dafe5923281009a022c0c81619dc9dc4d8.

### Task 1: review-plan comparability clause

Context surface: the plan's Terms, this task, and the origin row's Expected arm.

Files:
- `agents/skills/review-plan/SKILL.md`

Primary class anchors:
- `Scope and complexity policy` in `agents/skills/review-plan/SKILL.md`
- `Reconciliation gate` in `agents/skills/review-plan/SKILL.md`

- [x] The Scope and complexity policy and the Reconciliation gate compare over the two most recent comparable rounds, with `comparable round` defined once by the two-arm test (coverage outcome neither `degraded` nor `failed`, and no panel row with a status other than `complete`) [class: IMPLEMENTATION_REQUIRED]
- [x] The continuation rule's "blocking count fell from the previous round" reads against the previous comparable round [class: IMPLEMENTATION_REQUIRED]
- [x] When fewer than two comparable rounds exist, the loop continues one round to establish the baseline instead of firing the trigger [class: IMPLEMENTATION_REQUIRED]
- [x] The round that runs the comparison records one prose line in its own round record naming the excluded window member, written at the same close pass that evaluates the trigger; the excluded round's already-closed record is never edited retroactively [class: IMPLEMENTATION_REQUIRED]
- [x] The amendment adds no incident narrative and cites no origin-row path (anti-growth: land the rule, not the story; zero citations satisfies the requirement and is preferred, a living backlog path is not a durable citation home) [class: REPOSITORY_TEST]
- [x] Commit: `review: churn trigger compares comparable rounds only` (aa1baffff) [class: IMPLEMENTATION_REQUIRED]

### Task 2: review-reconciliation trigger audit mirror

Context surface: the plan's Terms, this task, and the origin row's mirror arm.

Files:
- `agents/skills/review-reconciliation/SKILL.md`

Primary class anchors:
- `Trigger` in `agents/skills/review-reconciliation/SKILL.md`

- [x] The Trigger section gains one trailing audit note after the invocation-condition list, phrased as audit method rather than an invocation condition: when auditing a measured churn-trigger firing, coverage-degraded rounds are excluded from the comparison window and the window runs over the most recent comparable rounds; a window with fewer than two comparable rounds is a baseline gap, not a firing [class: IMPLEMENTATION_REQUIRED]
- [x] The note cites no round record or session id and adds no new invocation condition to the list [class: REPOSITORY_TEST]
- [x] Commit: `review: reconciliation audits churn firings over comparable rounds` (78a1ae262) [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-loop firing resolution through the owned definition

Context surface: the plan's Terms, this task, and the delegation pattern review-loop's exit criteria already use for review-plan's Scope and complexity policy.

Files:
- `agents/skills/review-loop/SKILL.md`

Primary class anchors:
- `Orchestration rules` in `agents/skills/review-loop/SKILL.md`

- [x] Rule 5's firing test stops restating the totals comparison inline: it fires when review-plan's measured churn trigger fires over its comparable-rounds window, resolved by pointer to the owned definition (the same delegation pattern the exit criteria use for the Scope and complexity policy) [class: IMPLEMENTATION_REQUIRED]
- [x] The inline duplicate totals comparison is deleted, not paraphrased (growth balance: the deletion pays the added definition sentence in Task 1) [class: REPOSITORY_TEST]
- [x] Commit: `review: review-loop churn firing resolves through the comparable-rounds window` (dc71e3de0) [class: IMPLEMENTATION_REQUIRED]
